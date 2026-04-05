package com.unofficial.geminigo

import android.animation.ObjectAnimator
import android.animation.ValueAnimator
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.os.Build
import android.os.Bundle
import android.service.voice.VoiceInteractionSession
import android.view.View
import android.view.animation.AccelerateDecelerateInterpolator
import android.view.animation.LinearInterpolator
import android.widget.TextView

/**
 * Spark Go Assistant Session - handles the overlay UI when assistant is triggered.
 */
class SparkGoAssistantSession(context: Context) : VoiceInteractionSession(context) {

    private lateinit var scrim: View
    private lateinit var bottomSheet: View
    private lateinit var gradientBorder: View
    private lateinit var promptBar: View
    private lateinit var micIcon: View
    private lateinit var sparkIcon: View
    private lateinit var greetingText: TextView
    private var gradientAnimator: ValueAnimator? = null


    override fun onCreateContentView(): View {
        val view = layoutInflater.inflate(R.layout.assistant_overlay, null)
        scrim = view.findViewById(R.id.scrim)
        bottomSheet = view.findViewById(R.id.bottomSheet)
        gradientBorder = view.findViewById(R.id.gradientBorder)
        promptBar = view.findViewById(R.id.promptBar)
        micIcon = view.findViewById(R.id.micIcon)
        sparkIcon = view.findViewById(R.id.sparkIcon)
        greetingText = view.findViewById(R.id.greetingText)

        setupInteractions()
        return view
    }

    private fun setupInteractions() {
        scrim.setOnClickListener {
            finish()
        }

        promptBar.setOnClickListener {
            openMainActivity(voiceRequest = false)
        }

        micIcon.setOnClickListener {
            openMainActivity(voiceRequest = true)
        }
        
        sparkIcon.setOnClickListener {
            openMainActivity(voiceRequest = false)
        }
    }

    private fun openMainActivity(voiceRequest: Boolean) {
        val intent = Intent(context, MainActivity::class.java)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        if (voiceRequest) {
            intent.putExtra("ACTION_VOICE_SEARCH", true)
        }
        
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.M) {
            startVoiceActivity(intent)
        } else {
            // Fallback for API 21, 22
            context.startActivity(intent)
        }
        finish()
    }

    override fun onShow(args: Bundle?, showFlags: Int) {
        super.onShow(args, showFlags)
        startEnterAnimation()
        startGradientAnimation()
    }

    override fun onHide() {
        super.onHide()
        gradientAnimator?.cancel()
    }

    private fun startEnterAnimation() {
        scrim.alpha = 0f
        scrim.animate().alpha(1f).setDuration(300).start()

        bottomSheet.translationY = 300f
        bottomSheet.animate()
            .translationY(0f)
            .setInterpolator(OvershootInterpolator(0.8f))
            .setDuration(500)
            .start()
    }

    private fun startGradientAnimation() {
        // Shifting color animation for the gradient border
        val matrix = Matrix()
        val colors = intArrayOf(
            0xFF4285F4.toInt(), // Blue
            0xFF9B30FF.toInt(), // Purple
            0xFFEA4335.toInt(), // Red
            0xFFFBBC04.toInt(), // Yellow
            0xFF4285F4.toInt()  // Blue
        )
        
        gradientAnimator = ValueAnimator.ofFloat(0f, 1f).apply {
            duration = 3000
            repeatCount = ValueAnimator.INFINITE
            interpolator = LinearInterpolator()
            // Periodic update logic if needed for future shader work
        }
        
        // Let's do a more visible "glow" animation
        val glowAnim = ObjectAnimator.ofFloat(gradientBorder, "alpha", 0.7f, 1.0f).apply {
            duration = 1500
            repeatCount = ValueAnimator.INFINITE
            repeatMode = ValueAnimator.REVERSE
            interpolator = AccelerateDecelerateInterpolator()
            start()
        }
    }
}
