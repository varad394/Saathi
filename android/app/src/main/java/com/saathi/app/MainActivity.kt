package com.saathi.app

import android.Manifest
import android.annotation.SuppressLint
import android.app.Activity
import android.content.Context
import android.content.Intent
import android.content.pm.PackageManager
import android.graphics.Color
import android.graphics.Typeface
import android.view.Gravity
import android.text.TextUtils
import android.text.Html
import android.graphics.drawable.GradientDrawable
import android.hardware.Sensor
import android.hardware.SensorEvent
import android.hardware.SensorEventListener
import android.hardware.SensorManager
import android.location.Location
import android.location.LocationListener
import android.location.LocationManager
import android.net.Uri
import android.os.Build
import android.os.Bundle
import android.os.SystemClock
import android.telephony.SmsManager
import android.util.Log
import android.view.View
import android.view.WindowManager
import android.widget.Button
import android.widget.CheckBox
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
import java.text.SimpleDateFormat
import java.util.Date
import java.util.Locale
import java.util.concurrent.Executors
import java.util.concurrent.ScheduledFuture
import java.util.concurrent.TimeUnit

/**
 * Saathi phone app.
 *  - Crash detection runs on the phone (CrashDetector). Only 3 events go to the backend: impact (pre-warm the agent),
 *    confirmed (join the call), cancel (false alarm).
 *  - Emergency screen: state + countdown from the backend, big I'M OK / I NEED HELP buttons, what is actually done.
 *  - SMS from the rider's own SIM: join links to Mom and the 112 teammate; location-only SMS if there is no data.
 *  - Settings (gear): backend URL, demo phone numbers, and all server settings, no redeploy.
 */
class MainActivity : Activity(), SensorEventListener, CrashDetector.Listener {
    private val tag = "Saathi"
    private val io = Executors.newSingleThreadExecutor()
    private val poller = Executors.newSingleThreadScheduledExecutor()
    private var pollTask: ScheduledFuture<*>? = null
    private var engine: RtcEngine? = null
    private var t0 = SystemClock.elapsedRealtime()
    private var firstAgentAudio = false

    private val detector = CrashDetector(this)
    private lateinit var sensors: SensorManager
    private var location: Location? = null
    private var speedKmh = 0f

    // Pre-warm handshake: the impact response (join info) and the confirmation can arrive in either order.
    private val lock = Any()
    private var pendingJoin: JSONObject? = null
    private var crashConfirmed = false
    private var inCall = false
    private var impactFailed = false
    private var offlineSmsSent = false
    private var impactBody: String = "{}"
    private var sceneSid: String? = null
    private val smsSent = mutableSetOf<String>()

    private lateinit var stateView: TextView
    private lateinit var emergency: LinearLayout
    private lateinit var countdown: TextView
    private lateinit var doneView: TextView
    private lateinit var transcriptView: TextView
    @Volatile private var serverSettings = JSONObject()
    private lateinit var liveView: TextView
    private lateinit var thrLabel: TextView
    private lateinit var graph: SensorGraphView
    private lateinit var logView: TextView
    private lateinit var scroll: ScrollView
    private lateinit var btnArm: Button

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        window.addFlags(WindowManager.LayoutParams.FLAG_KEEP_SCREEN_ON or WindowManager.LayoutParams.FLAG_SHOW_WHEN_LOCKED
                or WindowManager.LayoutParams.FLAG_TURN_SCREEN_ON)
        sensors = getSystemService(Context.SENSOR_SERVICE) as SensorManager
        buildUi()
        val need = arrayOf(Manifest.permission.RECORD_AUDIO, Manifest.permission.ACCESS_FINE_LOCATION, Manifest.permission.SEND_SMS)
            .filter { checkSelfPermission(it) != PackageManager.PERMISSION_GRANTED }
        if (need.isNotEmpty()) requestPermissions(need.toTypedArray(), 1) else startLocation()
    }

    override fun onResume() {
        super.onResume()
        io.execute { try { serverSettings = Net.get(this, "/settings") } catch (_: Exception) {} }  // e.g. noise suppression
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) = startLocation()

    // ---------------- UI ----------------
    private val dp get() = resources.displayMetrics.density
    private fun rounded(color: Int, radius: Float = 16f, stroke: Int? = null) = GradientDrawable().apply {
        setColor(color); cornerRadius = radius * dp; if (stroke != null) setStroke((1.5f * dp).toInt(), stroke)
    }
    private fun card(): LinearLayout = LinearLayout(this).apply {
        orientation = LinearLayout.VERTICAL
        val p = (14 * dp).toInt(); setPadding(p, p, p, p)
        background = rounded(Color.WHITE)
        elevation = 2 * dp
    }
    private fun cardParams() = LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, LinearLayout.LayoutParams.WRAP_CONTENT)
        .apply { bottomMargin = (12 * dp).toInt() }
    private fun label(t: String) = TextView(this).apply {
        text = t; textSize = 12f; setTextColor(Color.rgb(110, 110, 120)); setTypeface(null, Typeface.BOLD); letterSpacing = 0.08f
        setPadding(0, 0, 0, (6 * dp).toInt())
    }
    private fun pill(t: String, bg: Int, fg: Int = Color.WHITE, size: Float = 16f, onClick: () -> Unit) = Button(this).apply {
        text = t; textSize = size; setTextColor(fg); isAllCaps = false; setTypeface(null, Typeface.BOLD)
        background = rounded(bg, 28f); setOnClickListener { onClick() }
    }

    private fun buildUi() {
        val pad = (14 * dp).toInt()
        val page = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setBackgroundColor(Color.rgb(244, 245, 247)) }

        // Header
        val header = LinearLayout(this).apply {
            orientation = LinearLayout.HORIZONTAL; setBackgroundColor(Color.rgb(18, 18, 22)); setPadding(pad, pad, pad, pad)
            gravity = Gravity.CENTER_VERTICAL
        }
        val titles = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        titles.addView(TextView(this).apply { text = "Saathi"; textSize = 24f; setTextColor(Color.WHITE); setTypeface(null, Typeface.BOLD) })
        titles.addView(TextView(this).apply { text = "Crash responder · speaks your language"; textSize = 12f; setTextColor(Color.rgb(180, 180, 190)) })
        header.addView(titles, LinearLayout.LayoutParams(0, LinearLayout.LayoutParams.WRAP_CONTENT, 1f))
        header.addView(pill("Settings", Color.rgb(55, 55, 65), size = 14f) { startActivity(Intent(this, SettingsActivity::class.java)) })
        page.addView(header)

        val body = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(pad, pad, pad, pad) }

        // Status card
        stateView = TextView(this).apply {
            textSize = 20f; setTypeface(null, Typeface.BOLD); setTextColor(Color.WHITE)
            val p = (16 * dp).toInt(); setPadding(p, p, p, p)
        }
        body.addView(stateView, cardParams())

        // Emergency card (visible during an incident)
        emergency = card().apply { visibility = View.GONE }
        countdown = TextView(this).apply { textSize = 18f; setTextColor(Color.rgb(200, 90, 0)); setTypeface(null, Typeface.BOLD) }
        emergency.addView(countdown)
        val big = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; setPadding(0, (10 * dp).toInt(), 0, (10 * dp).toInt()) }
        val h = (72 * dp).toInt()
        big.addView(pill("I'M OK", Color.rgb(26, 127, 55), size = 22f) { io.execute { tryPost("/crash/rider_ok") } },
            LinearLayout.LayoutParams(0, h, 1f).apply { rightMargin = (10 * dp).toInt() })
        big.addView(pill("I NEED HELP", Color.rgb(198, 40, 40), size = 20f) { io.execute { tryPost("/crash/rider_help") } },
            LinearLayout.LayoutParams(0, h, 1f))
        emergency.addView(big)
        emergency.addView(label("WHAT SAATHI HAS DONE"))
        doneView = TextView(this).apply { textSize = 16f; setTextColor(Color.rgb(30, 30, 35)); setLineSpacing(4 * dp, 1f) }
        emergency.addView(doneView)
        emergency.addView(View(this).apply { setBackgroundColor(Color.rgb(230, 230, 235)) },
            LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, (1 * dp).toInt()).apply { topMargin = (12 * dp).toInt(); bottomMargin = (12 * dp).toInt() })
        emergency.addView(label("CONVERSATION"))
        transcriptView = TextView(this).apply {
            textSize = 16f; setTextColor(Color.rgb(30, 30, 35)); setLineSpacing(6 * dp, 1f)
            val p = (12 * dp).toInt(); setPadding(p, p, p, p); background = rounded(Color.rgb(246, 247, 250), 12f)
        }
        emergency.addView(transcriptView)
        val row3 = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL; setPadding(0, (12 * dp).toInt(), 0, 0) }
        row3.addView(pill("Call 112", Color.WHITE, Color.rgb(198, 40, 40)) { startActivity(Intent(Intent.ACTION_DIAL, Uri.parse("tel:112"))) }
            .apply { background = rounded(Color.WHITE, 28f, Color.rgb(198, 40, 40)) },
            LinearLayout.LayoutParams(0, (52 * dp).toInt(), 1f).apply { rightMargin = (10 * dp).toInt() })
        row3.addView(pill("End", Color.rgb(90, 90, 100)) { stop() }, LinearLayout.LayoutParams(0, (52 * dp).toInt(), 1f))
        emergency.addView(row3)
        body.addView(emergency, cardParams())

        // Detection card
        val det = card()
        det.addView(label("CRASH DETECTION"))
        val row = LinearLayout(this).apply { orientation = LinearLayout.HORIZONTAL }
        btnArm = pill("Arm detection", Color.rgb(11, 87, 208), size = 15f) { toggleArm() }
        row.addView(btnArm, LinearLayout.LayoutParams(0, (48 * dp).toInt(), 1f).apply { rightMargin = (8 * dp).toInt() })
        row.addView(pill("Simulate crash", Color.rgb(198, 40, 40), size = 15f) { simulate() }, LinearLayout.LayoutParams(0, (48 * dp).toInt(), 1f))
        det.addView(row)
        det.addView(CheckBox(this).apply {
            text = "Demo mode: skip the riding-speed check"; isChecked = detector.cfg.demoSkipSpeed
            setOnCheckedChangeListener { _, c -> detector.cfg.demoSkipSpeed = c }
        })
        thrLabel = TextView(this).apply { textSize = 13f; setTextColor(Color.rgb(90, 90, 100)) }
        det.addView(thrLabel)
        det.addView(SeekBar(this).apply {
            max = 60
            progress = ((detector.cfg.impactG - 1f) * 10).toInt()
            setOnSeekBarChangeListener(object : SeekBar.OnSeekBarChangeListener {
                override fun onProgressChanged(s: SeekBar?, p: Int, fromUser: Boolean) { setThreshold(1f + p / 10f) }
                override fun onStartTrackingTouch(s: SeekBar?) {}
                override fun onStopTrackingTouch(s: SeekBar?) {}
            })
        })
        graph = SensorGraphView(this)
        det.addView(graph, LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, (120 * dp).toInt()))
        liveView = TextView(this).apply { typeface = Typeface.MONOSPACE; textSize = 11f; setTextColor(Color.rgb(90, 90, 100)) }
        det.addView(liveView)
        body.addView(det, cardParams())

        // Technical log (hidden by default)
        logView = TextView(this).apply { typeface = Typeface.MONOSPACE; textSize = 10f; setTextColor(Color.rgb(60, 60, 70)) }
        scroll = ScrollView(this).apply { addView(logView); visibility = View.GONE }
        body.addView(TextView(this).apply {
            text = "Show technical log"; textSize = 13f; setTextColor(Color.rgb(11, 87, 208))
            setOnClickListener { scroll.visibility = if (scroll.visibility == View.GONE) View.VISIBLE else View.GONE }
        })
        body.addView(scroll, LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, (220 * dp).toInt()))

        page.addView(ScrollView(this).apply { addView(body) }, LinearLayout.LayoutParams(LinearLayout.LayoutParams.MATCH_PARENT, 0, 1f))
        setContentView(page)
        setThreshold(detector.cfg.impactG)
        showState(CrashDetector.State.DISARMED, "Tap Arm detection, or Simulate crash")
    }

    private fun setThreshold(g: Float) {
        detector.cfg.impactG = g
        graph.threshold = g
        thrLabel.text = "Impact threshold %.1f g · still %.1f s · tilt over %.0f°".format(g, detector.cfg.stillWindowS, detector.cfg.orientDeg)
    }

    private fun showState(s: CrashDetector.State, detail: String) = runOnUiThread {
        val (bg, title) = when (s) {
            CrashDetector.State.DISARMED -> Color.rgb(120, 124, 135) to "Detection off"
            CrashDetector.State.MONITORING -> Color.rgb(26, 127, 55) to "Watching for a crash"
            CrashDetector.State.IMPACT -> Color.rgb(230, 140, 0) to "Impact detected, checking…"
            CrashDetector.State.CONFIRMED -> Color.rgb(198, 40, 40) to "Crash detected"
        }
        stateView.background = rounded(bg)
        stateView.text = "$title\n$detail"
        btnArm.text = if (s == CrashDetector.State.DISARMED) "Arm detection" else "Disarm"
    }

    private fun log(msg: String) {
        val s = "[+%.2fs] %s".format((SystemClock.elapsedRealtime() - t0) / 1000.0, msg)
        Log.i(tag, s)
        runOnUiThread { logView.append(s + "\n"); scroll.post { scroll.fullScroll(ScrollView.FOCUS_DOWN) } }
    }

    private fun tryPost(path: String, body: String = "{}"): JSONObject? =
        try { Net.post(this, path, body) } catch (e: Exception) { log("ERROR $path: ${e.message}"); null }

    // ---------------- Sensors ----------------
    private fun toggleArm() {
        if (detector.state == CrashDetector.State.DISARMED) {
            val acc = sensors.getDefaultSensor(Sensor.TYPE_ACCELEROMETER)
            sensors.registerListener(this, acc, SensorManager.SENSOR_DELAY_GAME)
            detector.arm()
            log("armed: ${acc?.name}")
        } else {
            sensors.unregisterListener(this)
            detector.disarm()
        }
    }

    private var lastUi = 0L
    override fun onSensorChanged(e: SensorEvent) {
        val now = SystemClock.elapsedRealtime()
        val ax = e.values[0]; val ay = e.values[1]; val az = e.values[2]
        detector.onAccel(ax, ay, az, now)
        val g = kotlin.math.sqrt(ax * ax + ay * ay + az * az) / 9.81f
        graph.add(g)
        if (now - lastUi > 150) {
            lastUi = now
            val loc = location
            liveView.text = "|a| %.2f g  tilt %.0f°  speed %.0f km/h  gps %s".format(g, detector.lastAngleDeg, speedKmh,
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
        resetIncident()
        val body = JSONObject().put("peak_g", peakG.toDouble()).put("speed_kmh", speedKmh.toDouble())
        location?.let { body.put("lat", it.latitude).put("lon", it.longitude) }
        impactBody = body.toString()
        io.execute { startAgentForCrash("/crash/impact") }
    }

    override fun onConfirmed(peakG: Float, angleDeg: Float, stillStdG: Float) {
        graph.mark(2)
        log(">>> CRASH CONFIRMED")
        val retry: Boolean
        synchronized(lock) { crashConfirmed = true; if (pendingJoin != null) joinNow(); retry = impactFailed }
        if (retry) { log("agent start had failed - retrying"); io.execute { startAgentForCrash("/crash/impact") } }
        val body = JSONObject().put("peak_g", peakG.toDouble()).put("angle_deg", angleDeg.toDouble()).put("still_std_g", stillStdG.toDouble())
        Thread { tryPost("/crash/confirmed", body.toString()) }.start()
    }

    override fun onCancelled(reason: String) {
        graph.mark(3)
        synchronized(lock) { pendingJoin = null; crashConfirmed = false }
        io.execute { tryPost("/crash/cancel", JSONObject().put("reason", reason).toString()); log("agent stopped (false alarm)") }
    }

    private fun resetIncident() {
        synchronized(lock) { pendingJoin = null; crashConfirmed = false; impactFailed = false; inCall = false }
        offlineSmsSent = false
        smsSent.clear()
        sceneSid = null
    }

    private fun startAgentForCrash(path: String) {
        try {
            log("starting Saathi agent at ${Net.base(this)}")
            val s = Net.post(this, path, impactBody)
            sceneSid = s.optString("sid", null)
            log("agent ready ${s.optString("agent_id")} (${s.optString("status")})")
            synchronized(lock) { pendingJoin = s; impactFailed = false; if (crashConfirmed) joinNow() }
            startPolling()
        } catch (e: Exception) {
            log("ERROR starting agent: ${e.message}")
            val confirmed: Boolean
            synchronized(lock) { impactFailed = true; confirmed = crashConfirmed }
            if (confirmed) sendOfflineSms()  // no backend / no data: location by SMS from our own SIM
        }
    }

    /** Must be called holding [lock]. */
    private fun joinNow() {
        val s = pendingJoin ?: return
        if (inCall) return
        inCall = true
        log("joining Saathi's call")
        joinChannel(s.getString("app_id"), s.getString("channel"), s.getInt("uid"), s.getString("token"))
    }

    // Simulated crash without the sensors (demo on stage / testing)
    private fun simulate() {
        t0 = SystemClock.elapsedRealtime()
        resetIncident()
        io.execute {
            try {
                val s = Net.post(this, "/crash/simulate")
                sceneSid = s.optString("sid", null)
                log("simulated crash; agent ${s.optString("agent_id")}")
                synchronized(lock) { pendingJoin = s; crashConfirmed = true; joinNow() }
                startPolling()
            } catch (e: Exception) { log("ERROR simulate: ${e.message}") }
        }
    }

    // ---------------- Incident polling: emergency screen + SMS ----------------
    private fun startPolling() {
        pollTask?.cancel(false)
        pollTask = poller.scheduleWithFixedDelay({ pollOnce() }, 0, 1000, TimeUnit.MILLISECONDS)
    }

    private fun pollOnce() {
        val inc = try { Net.get(this, "/incident") } catch (e: Exception) { return }
        val state = inc.optString("state")
        if (state == "NONE") return
        val left = if (inc.isNull("rider_check_left")) null else inc.optDouble("rider_check_left")
        val actions = inc.optJSONObject("actions") ?: JSONObject()
        val done = StringBuilder()
        for (k in actions.keys()) {
            val a = actions.getJSONObject(k)
            val st = a.optString("status")
            val mark = if (st in setOf("briefed", "reached", "sent")) "✓" else if (st == "failed") "✗" else "…"
            done.append("$mark ${pretty(k)}: $st\n")
        }
        maybeSendLinks(inc)
        val tr = inc.optJSONArray("transcript")
        val convoHtml = StringBuilder()
        if (tr != null) for (i in maxOf(0, tr.length() - 8) until tr.length()) {
            val e = tr.getJSONObject(i)
            val saathi = e.optString("who") == "saathi"
            if (convoHtml.isNotEmpty()) convoHtml.append("<br>")
            convoHtml.append(if (saathi) "<font color='#0b57d0'><b>Saathi:</b> " else "<font color='#1e1e23'><b>You:</b> ")
                .append(TextUtils.htmlEncode(e.optString("text").trim())).append("</font>")
        }
        val dest = inc.optString("destination").takeIf { it.isNotBlank() && it != "null" }
        runOnUiThread {
            emergency.visibility = if (state in setOf("CLOSED", "CANCELLED")) View.GONE else View.VISIBLE
            val (bg, title) = when (state) {
                "IMPACT", "DETECTED", "RIDER_CHECK" -> Color.rgb(230, 140, 0) to "Are you okay?"
                "CANCEL_PENDING" -> Color.rgb(26, 127, 55) to "Cancelling the alert…"
                "BYSTANDER" -> Color.rgb(198, 40, 40) to "Help is being called"
                "COORDINATE" -> Color.rgb(198, 40, 40) to "Saathi is guiding the people with you"
                "HANDOVER" -> Color.rgb(11, 87, 208) to "Ambulance team is here"
                "CLOSED" -> Color.rgb(90, 90, 100) to "Incident closed"
                "CANCELLED" -> Color.rgb(26, 127, 55) to "Alert cancelled - you're okay"
                else -> Color.rgb(90, 90, 100) to state
            }
            stateView.background = rounded(bg)
            stateView.text = title + (dest?.let { "\nGoing to: $it" } ?: "")
            countdown.text = when {
                left != null -> "Calling family and ambulance in %.0f s\nunless you say you're okay".format(left)
                state == "CANCEL_PENDING" -> "Say \"help\" or tap I NEED HELP if you need it"
                else -> ""
            }
            countdown.visibility = if (countdown.text.isNullOrEmpty()) View.GONE else View.VISIBLE
            doneView.text = if (done.isEmpty()) "Nothing sent yet" else done.toString().trim()
            transcriptView.text = if (convoHtml.isEmpty()) Html.fromHtml("<i>Listening…</i>", Html.FROM_HTML_MODE_LEGACY)
                                  else Html.fromHtml(convoHtml.toString(), Html.FROM_HTML_MODE_LEGACY)
        }
        // CLOSED: the call is over. CANCELLED: Saathi keeps listening ~60 s for "help", so stay in the call and keep
        // polling (a "help" re-opens the alert); the next crash leaves this channel before joining its own.
        if (state == "CLOSED") {
            pollTask?.cancel(false)
            engine?.leaveChannel()
            synchronized(lock) { inCall = false }
            log("incident closed: left the call")
        }
    }

    private fun pretty(k: String) = when {
        k == "ambulance" -> "Ambulance (112)"
        k.startsWith("family:") -> "Family (${k.removePrefix("family:")})"
        else -> k.replace('_', ' ')
    }

    /** Text each newly started call's join link from the rider's own SIM (family -> Mom, ambulance -> 112 teammate). */
    private fun maybeSendLinks(inc: JSONObject) {
        val sessions = inc.optJSONArray("sessions") ?: return
        val p = Net.prefs(this)
        for (i in 0 until sessions.length()) {
            val s = sessions.getJSONObject(i)
            val sid = s.optString("sid")
            val link = s.optString("link")
            if (link.isBlank() || link == "null" || sid in smsSent || s.optString("status") !in setOf("running", "joined")) continue
            val role = s.optString("role")
            val number = p.getString(if (role == "family") "mom_phone" else "amb_phone", "") ?: ""
            smsSent.add(sid)
            if (number.isBlank()) { log("no phone set for $role (Settings) - link: ${Net.base(this)}$link"); continue }
            val text = smsText(inc, role) + " Join Saathi's live call: ${Net.base(this)}$link"
            sendSms(number, text, role)
        }
    }

    private fun smsText(inc: JSONObject?, role: String): String {
        val name = Net.prefs(this).getString("rider_name", "Rahul") ?: "Rahul"
        val loc = location
        val incLoc = inc?.optJSONObject("location")
        val lat = loc?.latitude ?: incLoc?.optDouble("lat")
        val lon = loc?.longitude ?: incLoc?.optDouble("lon")
        val where = if (lat != null && lon != null && !lat.isNaN()) " Location: https://maps.google.com/?q=%.5f,%.5f .".format(lat, lon) else ""
        val time = SimpleDateFormat("HH:mm", Locale.US).format(Date())
        return if (role == "ambulance") "SAATHI EMERGENCY (demo 112): two-wheeler crash at $time.$where"
        else "Saathi: $name had a road accident at $time.$where"
    }

    private fun sendOfflineSms() {
        if (offlineSmsSent) return
        offlineSmsSent = true
        val number = Net.prefs(this).getString("mom_phone", "") ?: ""
        if (number.isBlank()) { log("offline: no Mom phone in Settings"); return }
        sendSms(number, smsText(null, "family") + " Saathi has no internet. Please call 112 and call this phone.", "family-offline")
    }

    @SuppressLint("MissingPermission")
    private fun sendSms(number: String, text: String, label: String) {
        if (checkSelfPermission(Manifest.permission.SEND_SMS) != PackageManager.PERMISSION_GRANTED) {
            log("SMS permission missing - not sent to $label"); return
        }
        try {
            val sms = if (Build.VERSION.SDK_INT >= 31) getSystemService(SmsManager::class.java) else @Suppress("DEPRECATION") SmsManager.getDefault()
            sms.sendMultipartTextMessage(number, null, sms.divideMessage(text), null, null)
            log("SMS sent to $label")
        } catch (e: Exception) { log("SMS to $label failed: ${e.message}") }
    }

    // ---------------- Voice (Agora RTC) ----------------
    private val handler = object : IRtcEngineEventHandler() {
        override fun onJoinChannelSuccess(channel: String?, uid: Int, elapsed: Int) {
            log("joined $channel as $uid")
            sceneSid?.let { sid -> io.execute { tryPost("/api/s/$sid/joined") } }  // starts the 20 s rider-check window
        }
        override fun onUserJoined(uid: Int, elapsed: Int) = log("Saathi agent joined")
        override fun onUserOffline(uid: Int, reason: Int) = log("Saathi agent left")
        override fun onError(err: Int) = log("RTC error $err: ${RtcEngine.getErrorDescription(err)}")
        override fun onRemoteAudioStateChanged(uid: Int, state: Int, reason: Int, elapsed: Int) {
            if (state == Constants.REMOTE_AUDIO_STATE_DECODING && !firstAgentAudio) {
                firstAgentAudio = true
                log(">>> FIRST SAATHI AUDIO (since impact/start)")
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
                mAudioScenario = Constants.AUDIO_SCENARIO_AI_CLIENT
            })
        }
        val e = engine!!
        e.leaveChannel()  // a previous crash's channel would make this join fail with -17 (already in a channel)
        e.enableAudio()
        e.setDefaultAudioRoutetoSpeakerphone(true)
        // AI noise suppression for loud roads / venues (settings: mic_ans on/off, ains_mode 0/1/2)
        val ains = serverSettings.optBoolean("mic_ans", true)
        val mode = serverSettings.optInt("ains_mode", 1)
        val rc0 = e.setAINSMode(ains, mode)
        log("AI noise suppression ${if (ains) "on, mode $mode" else "off"} (rc=$rc0)")
        // Loud roads: boost Saathi's voice on the loudspeaker; mic level adjustable (settings playback_gain / mic_gain)
        e.adjustPlaybackSignalVolume(serverSettings.optInt("playback_gain", 300))
        e.adjustRecordingSignalVolume(serverSettings.optInt("mic_gain", 100))
        val rc = e.joinChannel(token, channel, uid, ChannelMediaOptions().apply {
            clientRoleType = Constants.CLIENT_ROLE_BROADCASTER
            channelProfile = Constants.CHANNEL_PROFILE_COMMUNICATION
            publishMicrophoneTrack = true
            autoSubscribeAudio = true
        })
        log(if (rc == 0) "joining channel $channel" else "joinChannel FAILED rc=$rc (${RtcEngine.getErrorDescription(-rc)})")
    }

    private fun stop() = io.execute {
        tryPost("/incident/stop")
        engine?.leaveChannel()
        pollTask?.cancel(false)
        resetIncident()
        detector.rearm()
        runOnUiThread { emergency.visibility = View.GONE }
        log("ended")
    }

    override fun onDestroy() {
        super.onDestroy()
        sensors.unregisterListener(this)
        pollTask?.cancel(false)
        engine?.leaveChannel()
        RtcEngine.destroy()
        engine = null
    }
}
