package com.unofficial.geminigo

import android.animation.AnimatorSet
import android.animation.ObjectAnimator
import android.animation.ValueAnimator
import android.content.Context
import android.content.Intent
import android.graphics.Color
import android.graphics.LinearGradient
import android.graphics.Matrix
import android.graphics.Shader
import android.os.Bundle
import android.service.voice.VoiceInteractionSession
import android.view.View
import android.view.animation.AccelerateDecelerateInterpolator
import android.view.animation.LinearInterpolator
import android.view.animation.OvershootInterpolator
import android.widget.FrameLayout
import android.widget.LinearLayout
import android.widget.TextView

class GeminiAssistantSession(context: Context) : VoiceInteractionSession(context) {

    private lateinit var scrim: View
    private lateinit var bottomSheet: LinearLayout
    private lateinit var fluidGlowBar: View
    private lateinit var openAppButton: View
    private lateinit var greetingText: TextView
    private var fluidAnimator: ValueAnimator? = null

    override fun onCreate() {
        super.onCreate()
        // No window features needed usually for overlay
    }

    override fun onCreateContentView(): View {
        val view = layoutInflater.inflate(R.layout.assistant_overlay, null)
        scrim = view.findViewById(R.id.scrim)
        bottomSheet = view.findViewById(R.id.bottomSheet)
        fluidGlowBar = view.findViewById(R.id.fluidGlowBar)
        openAppButton = view.findViewById(R.id.openAppButton)
        greetingText = view.findViewById(R.id.greetingText)

        setupInteractions()
        return view
    }

    private fun setupInteractions() {
        scrim.setOnClickListener {
            finish() // Tapping outside closes the overlay
        }

        openAppButton.setOnClickListener {
            openMainActivity()
        }
        
        fluidGlowBar.setOnClickListener {
             openMainActivity()
        }
    }

    private fun openMainActivity() {
        val intent = Intent(context, MainActivity::class.java)
        intent.addFlags(Intent.FLAG_ACTIVITY_NEW_TASK)
        startVoiceActivity(intent)
        finish() // Close overlay
    }

    override fun onShow(args: Bundle?, showFlags: Int) {
        super.onShow(args, showFlags)
        startEnterAnimation()
        startFluidBarAnimation()
    }

    override fun onHide() {
        super.onHide()
        fluidAnimator?.cancel()
    }

    private fun startEnterAnimation() {
        scrim.alpha = 0f
        scrim.animate().alpha(1f).setDuration(300).start()

        bottomSheet.translationY = 500f
        bottomSheet.animate()
            .translationY(0f)
            .setInterpolator(OvershootInterpolator(1.0f))
            .setDuration(400)
            .start()
    }

    private fun startFluidBarAnimation() {
        // Gemini Colors for the bar
        val colors = intArrayOf(
            0xFF4285F4.toInt(), // Blue
            0xFFEA4335.toInt(), // Red
            0xFFFBBC04.toInt(), // Yellow
            0xFF34A853.toInt(), // Green
             0xFF4285F4.toInt() // Blue again
        )

        // Using LinearGradient for the bar instead of Sweep, looks better for a horizontal bar
        val shader = LinearGradient(0f, 0f, 1000f, 0f, colors, null, Shader.TileMode.MIRROR)
        
        // We can't apply shader directly to a View's background if it's a color.
        // But we can apply it to a PaintDrawable or similar. 
        // EASIER WAY: Custom Drawable or simpler: 
        // Let's use a ShapeDrawable programmatically or just apply to a TextView/custom view paint.
        // Hack for View: use a ShapeDrawable with shader factory or update background drawable.
        
        // Simpler approach for this specific View: 
        // Apply shader to a Paint and draw... 
        // OR: Since I can't easily set shader on a plain View background without custom class,
        // I will animate the background GradientDrawable colors if simple, 
        // BUT user wants FLUID.
        
        // Let's try applying a BitmapShader or Gradient to the View's background Drawable if it's a PaintDrawable.
        // Implementation:
        // Actually, let's just use the `greetingText` paint which allows shaders easily, 
        // and make the BAR be a View with a custom Drawable.
        
        // Workaround to avoid complex custom Views in this single-file logic:
        // Apply the shader to `greetingText` too, to match the main app.
        // For the bar, we will animate it simply or use the same text shader trick if we had a text view acting as a bar.
        
        // Let's animate the `greetingText` with the fluid shader first (it's the "Gemini" text).
        val textShader = LinearGradient(0f, 0f, greetingText.textSize * 5, 0f, colors, null, Shader.TileMode.MIRROR)
        greetingText.paint.shader = textShader
        
        val matrix = Matrix()
        fluidAnimator = ValueAnimator.ofFloat(0f, 1000f).apply {
            duration = 2000
            repeatCount = ValueAnimator.INFINITE
            interpolator = LinearInterpolator()
            addUpdateListener { 
                val translate = it.animatedValue as Float
                matrix.setTranslate(translate, 0f)
                textShader.setLocalMatrix(matrix)
                greetingText.invalidate()
            }
            start()
        }
        
        // For the bar itself (fluidGlowBar):
        // Simple pulsing color animation for now as it's a plain View
        val colorAnim = ObjectAnimator.ofArgb(fluidGlowBar, "backgroundColor", 
            0xFF4285F4.toInt(), 0xFFEA4335.toInt(), 0xFFFBBC04.toInt(), 0xFF34A853.toInt())
        colorAnim.duration = 4000
        colorAnim.repeatCount = ValueAnimator.INFINITE
        colorAnim.repeatMode = ValueAnimator.REVERSE
        colorAnim.start()
    }
}
