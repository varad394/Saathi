package com.saathi.app

import kotlin.math.acos
import kotlin.math.sqrt

/**
 * On-device crash detector. Feed it raw accelerometer samples (m/s^2, gravity included).
 *
 *   MONITORING --(|a| > impactG, speed gate ok)--> IMPACT   [onImpact: backend pre-warms agent]
 *   IMPACT --(still for stillWindowS AND orientation changed > orientDeg)--> CONFIRMED [onConfirmed]
 *   IMPACT --(no stillness within maxWaitS, or still but upright as before)--> MONITORING [onCancelled]
 */
class CrashDetector(private val listener: Listener) {

    data class Config(
        var impactG: Float = 2.5f,
        var settleS: Float = 0.4f,
        var stillWindowS: Float = 2.5f,
        var stillTolG: Float = 0.12f,
        var orientDeg: Float = 45f,
        var maxWaitS: Float = 8f,
        var speedGateKmh: Float = 15f,
        var demoSkipSpeed: Boolean = true,
    )

    enum class State { DISARMED, MONITORING, IMPACT, CONFIRMED }

    interface Listener {
        fun onState(state: State, detail: String)
        fun onImpact(peakG: Float)
        fun onConfirmed(peakG: Float, angleDeg: Float, stillStdG: Float)
        fun onCancelled(reason: String)
    }

    val cfg = Config()
    var state = State.DISARMED
        private set
    var lastAngleDeg = 0f
        private set

    // Speed gate (fed from GPS)
    private var lastFastAtMs = 0L

    // Gravity estimate (low-pass) + history to know orientation *before* the impact
    private val grav = FloatArray(3)
    private var gravInit = false
    private val gravHist = ArrayDeque<Pair<Long, FloatArray>>()

    // Impact bookkeeping
    private var impactAtMs = 0L
    private var peakG = 0f
    private var preImpactGrav = FloatArray(3)
    private val stillBuf = ArrayDeque<Pair<Long, Float>>()

    fun arm() { reset(); set(State.MONITORING, "armed") }
    fun disarm() { set(State.DISARMED, "disarmed") }
    fun rearm() { if (state != State.DISARMED) { reset(); set(State.MONITORING, "re-armed") } }

    fun onSpeed(kmh: Float, nowMs: Long) { if (kmh >= cfg.speedGateKmh) lastFastAtMs = nowMs }

    private fun speedOk(nowMs: Long) = cfg.demoSkipSpeed || nowMs - lastFastAtMs < 10_000

    fun onAccel(ax: Float, ay: Float, az: Float, nowMs: Long) {
        val mag = sqrt(ax * ax + ay * ay + az * az)
        val g = mag / 9.81f

        // Low-pass gravity (alpha ~0.1 at 50 Hz ≈ 0.2 s time constant)
        if (!gravInit) { grav[0] = ax; grav[1] = ay; grav[2] = az; gravInit = true }
        else { grav[0] += 0.1f * (ax - grav[0]); grav[1] += 0.1f * (ay - grav[1]); grav[2] += 0.1f * (az - grav[2]) }

        when (state) {
            State.DISARMED, State.CONFIRMED -> return
            State.MONITORING -> {
                gravHist.addLast(nowMs to grav.copyOf())
                while (gravHist.isNotEmpty() && nowMs - gravHist.first().first > 2000) gravHist.removeFirst()
                if (g > cfg.impactG && speedOk(nowMs)) {
                    impactAtMs = nowMs
                    peakG = g
                    // Orientation reference: average gravity 1.5 s .. 0.5 s before impact
                    preImpactGrav = avgGrav(nowMs - 1500, nowMs - 500) ?: grav.copyOf()
                    stillBuf.clear()
                    set(State.IMPACT, "impact %.1f g".format(g))
                    listener.onImpact(g)
                }
            }
            State.IMPACT -> {
                if (g > peakG) peakG = g
                val sinceImpact = (nowMs - impactAtMs) / 1000f
                if (sinceImpact < cfg.settleS) return
                stillBuf.addLast(nowMs to g)
                val windowMs = (cfg.stillWindowS * 1000).toLong()
                while (stillBuf.isNotEmpty() && nowMs - stillBuf.first().first > windowMs) stillBuf.removeFirst()

                val span = stillBuf.last().first - stillBuf.first().first
                if (span >= windowMs - 60) {
                    val std = stdDev(stillBuf.map { it.second })
                    lastAngleDeg = angleDeg(preImpactGrav, grav)
                    if (std < cfg.stillTolG) {
                        if (lastAngleDeg >= cfg.orientDeg) {
                            set(State.CONFIRMED, "crash: peak %.1f g, tilt %.0f°, still σ=%.2f g".format(peakG, lastAngleDeg, std))
                            listener.onConfirmed(peakG, lastAngleDeg, std)
                        } else {
                            cancel("still but orientation changed only %.0f°".format(lastAngleDeg))
                        }
                        return
                    }
                }
                if (sinceImpact > cfg.maxWaitS) cancel("kept moving (no stillness in %.0f s)".format(cfg.maxWaitS))
            }
        }
    }

    private fun cancel(reason: String) {
        listener.onCancelled(reason)
        reset()
        set(State.MONITORING, "cancelled: $reason")
    }

    private fun reset() { stillBuf.clear(); gravHist.clear(); peakG = 0f; lastAngleDeg = 0f }

    private fun set(s: State, detail: String) { state = s; listener.onState(s, detail) }

    private fun avgGrav(fromMs: Long, toMs: Long): FloatArray? {
        val sel = gravHist.filter { it.first in fromMs..toMs }
        if (sel.isEmpty()) return null
        val out = FloatArray(3)
        sel.forEach { for (i in 0..2) out[i] += it.second[i] }
        for (i in 0..2) out[i] /= sel.size
        return out
    }

    companion object {
        fun angleDeg(a: FloatArray, b: FloatArray): Float {
            val na = sqrt(a[0] * a[0] + a[1] * a[1] + a[2] * a[2])
            val nb = sqrt(b[0] * b[0] + b[1] * b[1] + b[2] * b[2])
            if (na < 1e-3f || nb < 1e-3f) return 0f
            val c = ((a[0] * b[0] + a[1] * b[1] + a[2] * b[2]) / (na * nb)).coerceIn(-1f, 1f)
            return Math.toDegrees(acos(c).toDouble()).toFloat()
        }

        fun stdDev(v: List<Float>): Float {
            if (v.size < 2) return Float.MAX_VALUE
            val m = v.average().toFloat()
            return sqrt(v.sumOf { ((it - m) * (it - m)).toDouble() }.toFloat() / v.size)
        }
    }
}
