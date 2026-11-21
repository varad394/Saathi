package com.saathi.app

import android.app.Activity
import android.graphics.Typeface
import android.os.Bundle
import android.text.InputType
import android.view.View
import android.widget.Button
import android.widget.CheckBox
import android.widget.EditText
import android.widget.LinearLayout
import android.widget.ScrollView
import android.widget.TextView
import android.widget.Toast
import org.json.JSONObject
import java.util.concurrent.Executors

/**
 * Settings without a redeploy:
 *  - On this phone: backend URL, rider name, demo phone numbers (Mom, 112 teammate). Numbers never leave the phone
 *    except in the SMS itself.
 *  - On the server (GET/POST /settings): speech-to-text vendor, voice detection, mic processing, timers.
 */
class SettingsActivity : Activity() {
    private val io = Executors.newSingleThreadExecutor()
    private val local = linkedMapOf(
        "url" to "Backend URL",
        "rider_name" to "Rider name (for SMS)",
        "mom_phone" to "Mother's phone (+91…)",
        "amb_phone" to "112 teammate's phone (+91…)",
    )
    private val localFields = mutableMapOf<String, EditText>()
    private val serverFields = mutableMapOf<String, View>()
    private lateinit var serverBox: LinearLayout
    private var serverTypes = JSONObject()

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        val d = resources.displayMetrics.density
        val pad = (14 * d).toInt()
        val root = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL; setPadding(pad, pad, pad, pad) }
        root.addView(TextView(this).apply { text = "Saathi settings"; textSize = 22f; setTypeface(null, Typeface.BOLD) })

        root.addView(header("On this phone"))
        val p = Net.prefs(this)
        for ((k, label) in local) {
            root.addView(TextView(this).apply { text = label; textSize = 13f })
            val et = EditText(this).apply {
                setText(if (k == "url") Net.base(this@SettingsActivity) else p.getString(k, if (k == "rider_name") "Rahul" else "") ?: "")
                isSingleLine = true
                if (k.endsWith("phone")) inputType = InputType.TYPE_CLASS_PHONE
            }
            localFields[k] = et
            root.addView(et)
        }

        root.addView(header("On the server (apply to the next crash)"))
        serverBox = LinearLayout(this).apply { orientation = LinearLayout.VERTICAL }
        root.addView(serverBox)

        root.addView(Button(this).apply { text = "Save"; setOnClickListener { save() } })
        root.addView(Button(this).apply { text = "Reset server settings"; setOnClickListener { resetServer() } })
        root.addView(Button(this).apply { text = "Reload from server"; setOnClickListener { loadServer() } })
        setContentView(ScrollView(this).apply { addView(root) })
        loadServer()
    }

    private fun header(t: String) = TextView(this).apply {
        text = t; textSize = 16f; setTypeface(null, Typeface.BOLD); setPadding(0, 24, 0, 6)
    }

    private fun toast(msg: String) = runOnUiThread { Toast.makeText(this, msg, Toast.LENGTH_SHORT).show() }

    private fun loadServer() = io.execute {
        try {
            val st = Net.get(this, "/settings")
            runOnUiThread { render(st) }
        } catch (e: Exception) {
            toast("Server settings unavailable: ${e.message}")
        }
    }

    private fun render(st: JSONObject) {
        serverTypes = st
        serverBox.removeAllViews()
        serverFields.clear()
        for (k in st.keys()) {
            val v = st.get(k)
            if (v is Boolean) {
                val cb = CheckBox(this).apply { text = k; isChecked = v }
                serverFields[k] = cb
                serverBox.addView(cb)
            } else {
                serverBox.addView(TextView(this).apply { text = k; textSize = 13f })
                val et = EditText(this).apply { setText(v.toString()); isSingleLine = true }
                serverFields[k] = et
                serverBox.addView(et)
            }
        }
    }

    private fun save() {
        val e = Net.prefs(this).edit()
        for ((k, et) in localFields) e.putString(k, et.text.toString().trim())
        e.putString("url_build", BuildConfig.BACKEND_URL)
        e.apply()
        val patch = JSONObject()
        for ((k, v) in serverFields) patch.put(k, if (v is CheckBox) v.isChecked else (v as EditText).text.toString().trim())
        io.execute {
            try {
                render2(Net.post(this, "/settings", patch.toString()))
                toast("Saved")
            } catch (ex: Exception) {
                toast("Saved on phone; server: ${ex.message}")
            }
        }
    }

    private fun render2(st: JSONObject) = runOnUiThread { render(st) }

    private fun resetServer() = io.execute {
        try {
            render2(Net.post(this, "/settings/reset"))
            toast("Server settings reset")
        } catch (e: Exception) {
            toast("Reset failed: ${e.message}")
        }
    }
}
