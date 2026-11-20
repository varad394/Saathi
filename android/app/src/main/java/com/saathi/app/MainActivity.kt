package com.saathi.app

import android.Manifest
import android.annotation.SuppressLint
import android.app.Activity
import android.content.Context
import android.content.pm.PackageManager
import android.graphics.Color
import android.graphics.Typeface
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.os.Bundle
import android.os.SystemClock
import android.util.Log
import android.view.WindowManager
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.SeekBar
import android.widget.TextView
import io.agora.rtc2.ChannelMediaOptions
import io.agora.rtc2.Constants
import io.agora.rtc2.IRtcEngineEventHandler
import io.agora.rtc2.RtcEngine
import io.agora.rtc2.RtcEngineConfig
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL
import java.util.concurrent.Executors

/**
 * Saathi barebones client.
 *  - Crash detection runs fully on the phone (CrashDetector); only 3 events go to the backend:
 *    impact (pre-warm agent), confirmed (join channel), cancel (stop agent).
 *  - Voice: joins the agent's Agora channel on loudspeaker.
 * Backend default is http://127.0.0.1:8000 via `adb reverse tcp:8000 tcp:8000`.
 */
class MainActivity : Activity(), SensorEventListener, CrashDetector.Listener {
    private val tag = "Saathi"
    private val io = Executors.newSingleThreadExecutor()
    private var engine: RtcEngine? = null
    private var t0 = SystemClock.elapsedRealtime()
    private var firstAgentAudio = false

    private val detector = CrashDetector(this)
    private lateinit var sensors: SensorManager
    private var location: Location? = null
    private var speedKmh = 0f

    // Pre-warm handshake: impact response (join info) and confirmation can arrive in either order.
    private val lock = Any()
    private var pendingJoin: JSONObject? = null
    private var crashConfirmed = false
    private var inCall = false
    private var impactFailed = false
    private var impactBody: String = "{}"

    private lateinit var urlField: EditText
    private lateinit var stateView: TextView
    private lateinit var liveView: TextView
    private lateinit var thrLabel: TextView
    private lateinit var graph: SensorGraphView
    private lateinit var logView: TextView
    private lateinit var scroll: ScrollView
    private lateinit var btnArm: Button
    private lateinit var btnStart: Button
    private lateinit var btnSpeak: Button
    private lateinit var btnStop: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON or WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED)
        sensors = getSystemService(Context.SENSOR_SERVICE) as SensorManager
        buildUi()
        val need = arrayOf(Manifest.permission.RECORD_AUDIO, Manifest.permission.ACCESS_FINE_LOCATION)
            .filter { checkSelfPermission(it) != PackageManager.PERMISSION_GRANTED }
        if (need.isNotEmpty()) requestPermissions(need.toTypedArray(), 1) else startLocation()
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        startLocation()
    }

    // ---------------- UI ----------------
    private fun buildUi() {
        val d = resources.displayMetrics.density
        val pad = (12 * d).toInt()
        val root = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(pad, pad, pad, pad) }
        stateView = TextView(this).apply { textSize = 20f; setTypeface(null, Typeface.BOLD); setPadding(pad, pad / 2, pad, pad / 2) }
        root.addView(stateView)

        val row = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        btnArm = Button(this).apply { text = "Arm detection"; setOnClickListener { toggleArm() } }
        val demo = CheckBox(this).apply {
            text = "Demo: skip speed gate"; isChecked = detector.cfg.demoSkipSpeed
            setOnCheckedChangeListener { _, c -> detector.cfg.demoSkipSpeed = c }
        }
        row.addView(btnArm); row.addView(demo)
        root.addView(row)

        thrLabel = TextView(this)
        root.addView(thrLabel)
        root.addView(SeekBar(this).apply {
            max = 60 // 1.0 .. 7.0 g in 0.1 steps
            progress = ((detector.cfg.impactG - 1f) * 10).toInt()
            setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
                override fun onProgressChanged(s: SeekBar?, p: Int, fromUser: Boolean) { setThreshold(1f + p / 10f) }
                override fun onStartTrackingTouch(s: SeekBar?) {}
                override fun onStopTrackingTouch(s: SeekBar?) {}
            })
        })

        graph = SensorGraphView(this)
        root.addView(graph, LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, (150 * d).toInt()))
        liveView = TextView(this).apply { typeface = Typeface.MONOSPACE; textSize = 12f }
        root.addView(liveView)

        urlField = EditText(this).apply {
            setText(getSharedPreferences("saathi", MODE_PRIVATE).getString("url", null) ?: BuildConfig.BACKEND_URL)
            textSize = 13f; isSingleLine = true
        }
        root.addView(urlField)
        val row2 = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        btnStart = Button(this).apply { text = "Manual start"; setOnClickListener { manualStart() } }
        btnSpeak = Button(this).apply { text = "First-aid line"; isEnabled = false; setOnClickListener { speak() } }
        btnStop = Button(this).apply { text = "Stop"; isEnabled = false; setOnClickListener { stop() } }
        listOf(btnStart, btnSpeak, btnStop).forEach { row2.addView(it, LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f)) }
        root.addView(row2)

        logView = TextView(this).apply { typeface = Typeface.MONOSPACE; textSize = 10f }
        scroll = ScrollView(this).apply { addView(logView) }
        root.addView(scroll, LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f))
        setContentView(root)
        baseUrl = urlField.text.toString().trim().trimEnd('/')
        urlField.addTextChangedListener(object : android.text.TextWatcher {
            override fun afterTextChanged(s: android.text.Editable?) {
                baseUrl = s.toString().trim().trimEnd('/')
                getSharedPreferences("saathi", MODE_PRIVATE).edit().putString("url", baseUrl).apply()
            }
            override fun beforeTextChanged(s: CharSequence?, a: Int, b: Int, c: Int) {}
            override fun onTextChanged(s: CharSequence?, a: Int, b: Int, c: Int) {}
        })
        setThreshold(detector.cfg.impactG)
        showState(CrashDetector.State.DISARMED, "tap Arm")
    }

    private fun setThreshold(g: Float) {
        detector.cfg.impactG = g
        graph.threshold = g
        thrLabel.text = "Impact threshold: %.1f g   (still %.1fs, tilt >%.0f°)".format(g, detector.cfg.stillWindowS, detector.cfg.orientDeg)
    }

    private fun showState(s: CrashDetector.State, detail: String) = runOnUiThread {
        val (bg, label) = when (s) {
            CrashDetector.State.DISARMED -> Color.LTGRAY to "DISARMED"
            CrashDetector.State.MONITORING -> Color.rgb(170, 225, 180) to "MONITORING"
            CrashDetector.State.IMPACT -> Color.rgb(255, 200, 90) to "IMPACT - checking…"
            CrashDetector.State.CONFIRMED -> Color.rgb(240, 90, 90) to "CRASH DETECTED"
        }
        stateView.setBackgroundColor(bg); stateView.setTextColor(Color.BLACK)
        stateView.text = "$label\n$detail"
        btnArm.text = if (s == CrashDetector.State.DISARMED) "Arm detection" else "Disarm"
    }

    private fun log(msg: String) {
        val s = "[+%.2fs] %s".format((SystemClock.elapsedRealtime() - t0) / 1000.0, msg)
        Log.i(tag, s)
        runOnUiThread { logView.append(s + "\n"); scroll.post { scroll.fullScroll(ScrollView.FOCUS_DOWN) } }
    }

    // ---------------- Sensors ----------------
    private fun toggleArm() {
        if (detector.state == CrashDetector.State.DISARMED) {
            val acc = sensors.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
            sensors.registerListener(this, acc, SensorManager.SENSOR_DELAY_GAME)
            detector.arm()
            log("armed: accelerometer ${acc?.name}")
        } else {
            sensors.unregisterListener(this)
            detector.disarm()
        }
    }

    private var lastUi = 0L
    override fun onSensorChanged(e: SensorEvent) {
        val now = SystemClock.elapsedRealtime()
        val (ax, ay, az) = Triple(e.values[0], e.values[1], e.values[2])
        detector.onAccel(ax, ay, az, now)
        val g = kotlin.math.sqrt(ax * ax + ay * ay + az * az) / 9.81f
        graph.add(g)
        if (now - lastUi > 150) {
            lastUi = now
            val loc = location
            liveView.text = "|a| %.2f g  tilt %.0f°  speed %.0f km/h  gps %s".format(
                g, detector.lastAngleDeg, speedKmh,
                if (loc != null) "%.4f,%.4f".format(loc.latitude, loc.longitude) else "—")
        }
    }

    override fun onAccuracyChanged(s: Sensor?, a: Int) {}

    @SuppressLint("MissingPermission")
    private fun startLocation() {
        if (checkSelfPermission(Manifest.permission.ACCESS_FINE_LOCATION) != PackageManager.PERMISSION_GRANTED) return
        val lm = getSystemService(Context.LOCATION_SERVICE) as LocationManager
        val l = LocationListener { loc ->
            location = loc
            speedKmh = if (loc.hasSpeed()) loc.speed * 3.6f else 0f
            detector.onSpeed(speedKmh, SystemClock.elapsedRealtime())
        }
        for (p in listOf(LocationManager.GPS_PROVIDER, LocationManager.NETWORK_PROVIDER)) {
            if (lm.isProviderEnabled(p)) {
                lm.requestLocationUpdates(p, 1000L, 0f, l)
                lm.getLastKnownLocation(p)?.let { if (location == null) location = it }
            }
        }
    }

    // ---------------- Detector callbacks ----------------
    override fun onState(state: CrashDetector.State, detail: String) {
        showState(state, detail)
        log("detector: $state - $detail")
    }

    override fun onImpact(peakG: Float) {
        t0 = SystemClock.elapsedRealtime()
        graph.mark(1)
        synchronized(lock) { pendingJoin = null; crashConfirmed = false; impactFailed = false }
        val body = JSONObject().put("peak_g", peakG.toDouble()).put("speed_kmh", speedKmh.toDouble())
        location?.let { body.put("lat", it.latitude).put("lon", it.longitude) }
        impactBody = body.toString()
        io.execute { startAgentForCrash() }
    }

    private fun startAgentForCrash() {
        run {
            try {
                log("impact -> pre-warming agent at ${base()}")
                val s = post("/crash/impact", impactBody)
                log("agent ready ${s.optString("agent_id")} (${s.optString("status")})")
                synchronized(lock) { pendingJoin = s; if (crashConfirmed) joinNow() }
            } catch (e: Exception) {
                synchronized(lock) { impactFailed = true }
                log("ERROR impact: ${e.message}"); netError(e.message)
            }
        }
    }

    private fun netError(msg: String?) = runOnUiThread {
        stateView.setBackgroundColor(Color.rgb(200, 0, 0)); stateView.setTextColor(Color.WHITE)
        stateView.text = "${stateView.text}\nBACKEND UNREACHABLE: $msg"
    }

    override fun onConfirmed(peakG: Float, angleDeg: Float, stillStdG: Float) {
        graph.mark(2)
        log(">>> CRASH CONFIRMED")
        val retry: Boolean
        synchronized(lock) { crashConfirmed = true; if (pendingJoin != null) joinNow(); retry = impactFailed }
        if (retry) { log("impact start had failed - retrying now"); io.execute { startAgentForCrash() } }
        val body = JSONObject().put("peak_g", peakG.toDouble()).put("angle_deg", angleDeg.toDouble()).put("still_std_g", stillStdG.toDouble())
        Thread { try { post("/crash/confirmed", body.toString()) } catch (e: Exception) { log("ERROR confirm: ${e.message}") } }.start()
    }

    override fun onCancelled(reason: String) {
        graph.mark(3)
        synchronized(lock) { pendingJoin = null; crashConfirmed = false }
        io.execute {
            try { post("/crash/cancel", JSONObject().put("reason", reason).toString()); log("agent stopped (false alarm)") }
            catch (e: Exception) { log("ERROR cancel: ${e.message}") }
        }
    }

    /** Must be called holding [lock]. */
    private fun joinNow() {
        val s = pendingJoin ?: return
        if (inCall) return
        inCall = true
        log("joining agent channel")
        joinChannel(s.getString("app_id"), s.getString("channel"), s.getInt("uid"), s.getString("token"))
    }

    // ---------------- Network ----------------
    @Volatile private var baseUrl = ""
    private fun base(): String = baseUrl

    private fun post(path: String, body: String = "{}"): JSONObject {
        if (baseUrl.isEmpty()) throw RuntimeException("backend URL not set")
        val c = URL(base() + path).openConnection() as HttpURLConnection
        c.requestMethod = "POST"; c.connectTimeout = 8000; c.readTimeout = 20000; c.doOutput = true
        c.setRequestProperty("Content-Type", "application/json")
        c.outputStream.use { it.write(body.toByteArray()) }
        val ok = c.responseCode in 200..299
        val text = (if (ok) c.inputStream else c.errorStream)?.bufferedReader()?.readText() ?: ""
        if (!ok) throw RuntimeException("$path -> ${c.responseCode} $text")
        return JSONObject(text)
    }

    // ---------------- Voice (Agora RTC) ----------------
    private fun manualStart() {
        t0 = SystemClock.elapsedRealtime()
        io.execute {
            try {
                log("POST /session/start ...")
                val s = post("/session/start")
                log("agent ${s.optString("agent_id")} ${s.optString("status")}")
                synchronized(lock) { pendingJoin = s; crashConfirmed = true; joinNow() }
            } catch (e: Exception) { log("ERROR ${e.message}") }
        }
    }

    private val handler = object : IRtcEngineEventHandler() {
        override fun onJoinChannelSuccess(channel: String?, uid: Int, elapsed: Int) {
            log("joined $channel as $uid; speakerphone=${engine?.isSpeakerphoneEnabled}")
            runOnUiThread { btnSpeak.isEnabled = true; btnStop.isEnabled = true; btnStart.isEnabled = false }
        }
        override fun onUserJoined(uid: Int, elapsed: Int) = log("agent uid $uid joined")
        override fun onUserOffline(uid: Int, reason: Int) = log("agent uid $uid left, reason=$reason")
        override fun onError(err: Int) = log("RTC error $err: ${RtcEngine.getErrorDescription(err)}")
        override fun onRemoteAudioStateChanged(uid: Int, state: Int, reason: Int, elapsed: Int) {
            if (state == Constants.REMOTE_AUDIO_STATE_DECODING && !firstAgentAudio) {
                firstAgentAudio = true
                log(">>> FIRST AGENT AUDIO (t since impact/start)")
            }
        }
    }

    private fun joinChannel(appId: String, channel: String, uid: Int, token: String) {
        firstAgentAudio = false
        if (engine == null) {
            engine = RtcEngine.create(RtcEngineConfig().apply {
                mContext = applicationContext
                mAppId = appId
                mEventHandler = handler
                mChannelProfile = Constants.CHANNEL_PROFILE_COMMUNICATION
                mAudioScenario = Constants.AUDIO_SCENARIO_AI_CLIENT // tuned for talking to AI agents
            })
        }
        val e = engine!!
        e.enableAudio()
        e.setDefaultAudioRoutetoSpeakerphone(true) // loudspeaker from the first frame
        val rc = e.joinChannel(token, channel, uid, ChannelMediaOptions().apply {
            clientRoleType = Constants.CLIENT_ROLE_BROADCASTER
            channelProfile = Constants.CHANNEL_PROFILE_COMMUNICATION
            publishMicrophoneTrack = true
            autoSubscribeAudio = true
        })
        log("joinChannel rc=$rc")
    }

    private fun speak() = io.execute {
        try { log("speak -> ${post("/session/speak").optString("text")}") } catch (e: Exception) { log("ERROR ${e.message}") }
    }

    private fun stop() = io.execute {
        try { post("/session/stop"); log("agent stopped") } catch (e: Exception) { log("ERROR ${e.message}") }
        engine?.leaveChannel()
        synchronized(lock) { inCall = false; pendingJoin = null; crashConfirmed = false }
        detector.rearm()
        runOnUiThread { btnStart.isEnabled = true; btnSpeak.isEnabled = false; btnStop.isEnabled = false }
    }

    override fun onDestroy() {
        super.onDestroy()
        sensors.unregisterListener(this)
        engine?.leaveChannel()
        RtcEngine.destroy()
        engine = null
    }
}
