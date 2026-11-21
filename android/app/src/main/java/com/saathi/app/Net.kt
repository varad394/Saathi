package com.saathi.app

import android.content.Context
import org.json.JSONObject
import java.net.HttpURLConnection
import java.net.URL

/** Tiny HTTP helper + local preferences (backend URL and demo phone numbers live only on the phone). */
object Net {
    fun prefs(c: Context) = c.getSharedPreferences("saathi", Context.MODE_PRIVATE)

    /** A URL typed in Settings wins, but only for the build it was typed in (a new tunnel = a new build). */
    fun base(c: Context): String {
        val p = prefs(c)
        val saved = p.getString("url", null)
        val forBuild = p.getString("url_build", null)
        return (if (!saved.isNullOrBlank() && forBuild == BuildConfig.BACKEND_URL) saved else BuildConfig.BACKEND_URL).trim().trimEnd('/')
    }

    fun post(c: Context, path: String, body: String = "{}"): JSONObject = call(c, "POST", path, body)
    fun get(c: Context, path: String): JSONObject = call(c, "GET", path, null)

    private fun call(c: Context, method: String, path: String, body: String?): JSONObject {
        val conn = URL(base(c) + path).openConnection() as HttpURLConnection
        conn.requestMethod = method
        conn.connectTimeout = 8000
        conn.readTimeout = 20000
        if (body != null) {
            conn.doOutput = true
            conn.setRequestProperty("Content-Type", "application/json")
            conn.outputStream.use { it.write(body.toByteArray()) }
        }
        val ok = conn.responseCode in 200..299
        val text = (if (ok) conn.inputStream else conn.errorStream)?.bufferedReader()?.readText() ?: ""
        if (!ok) throw RuntimeException("$path -> ${conn.responseCode} ${text.take(200)}")
        return if (text.isBlank()) JSONObject() else JSONObject(text)
    }
}
