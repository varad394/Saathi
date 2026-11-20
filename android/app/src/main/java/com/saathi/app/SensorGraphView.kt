package com.saathi.app

import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.DashPathEffect
import android.graphics.Paint
import android.graphics.Path
import android.view.View

/** Scrolling plot of |a| in g for the last ~10 s, with the impact threshold and event markers. */
class SensorGraphView(context: Context) : View(context) {
    private val n = 500 // 10 s at ~50 Hz
    private val vals = FloatArray(n)
    private val marks = IntArray(n) // 0 none, 1 impact, 2 confirmed, 3 cancelled
    private var head = 0
    var threshold = 2.5f
    private val maxG = 5f
    private val dp = context.resources.displayMetrics.density

    private val line = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.rgb(20, 120, 220); strokeWidth = 2 * dp; style = Paint.Style.STROKE }
    private val thr = Paint().apply { color = Color.rgb(220, 50, 50); strokeWidth = 1.5f * dp; pathEffect = DashPathEffect(floatArrayOf(10f, 8f), 0f) }
    private val grid = Paint().apply { color = Color.LTGRAY; strokeWidth = 1f }
    private val text = Paint(Paint.ANTI_ALIAS_FLAG).apply { color = Color.DKGRAY; textSize = 11 * dp }
    private val markPaint = arrayOf(Paint(), Paint().apply { color = Color.rgb(240, 140, 0); strokeWidth = 2 * dp },
        Paint().apply { color = Color.rgb(200, 0, 0); strokeWidth = 3 * dp }, Paint().apply { color = Color.rgb(0, 160, 80); strokeWidth = 2 * dp })
    private val path = Path()

    @Synchronized fun add(g: Float) { vals[head] = g; marks[head] = 0; head = (head + 1) % n; postInvalidateOnAnimation() }
    @Synchronized fun mark(kind: Int) { marks[(head - 1 + n) % n] = kind }

    @Synchronized override fun onDraw(c: Canvas) {
        val w = width.toFloat(); val h = height.toFloat()
        c.drawColor(Color.rgb(250, 250, 250))
        fun y(g: Float) = h - (g.coerceIn(0f, maxG) / maxG) * h
        for (g in 1..4) { c.drawLine(0f, y(g.toFloat()), w, y(g.toFloat()), grid); c.drawText("${g}g", 4 * dp, y(g.toFloat()) - 2 * dp, text) }
        c.drawLine(0f, y(threshold), w, y(threshold), thr)
        c.drawText("impact %.1fg".format(threshold), w - 90 * dp, y(threshold) - 4 * dp, text)
        path.reset()
        for (i in 0 until n) {
            val idx = (head + i) % n
            val x = i * w / (n - 1)
            if (i == 0) path.moveTo(x, y(vals[idx])) else path.lineTo(x, y(vals[idx]))
            if (marks[idx] != 0) c.drawLine(x, 0f, x, h, markPaint[marks[idx]])
        }
        c.drawPath(path, line)
    }
}
