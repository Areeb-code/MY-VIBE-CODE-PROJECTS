package com.unofficial.geminigo

import android.animation.ValueAnimator
import android.content.Context
import android.graphics.Canvas
import android.graphics.Color
import android.graphics.Paint
import android.graphics.RadialGradient
import android.graphics.Shader
import android.util.AttributeSet
import android.view.View
import android.view.animation.LinearInterpolator
import kotlin.math.cos
import kotlin.math.sin
import kotlin.random.Random

/**
 * Custom View that renders an animated fire effect with fluid, 
 * water-like particle movement and color fluctuations.
 */
class FireAnimationView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : View(context, attrs, defStyleAttr) {

    // Spark Go logo colors - Blue, Purple, Red, Yellow
    private val fireColors = intArrayOf(
        Color.parseColor("#4285F4"),  // Google Blue
        Color.parseColor("#9B30FF"),  // Purple
        Color.parseColor("#EA4335"),  // Red
        Color.parseColor("#FBBC04"),  // Yellow
        Color.parseColor("#34A853"),  // Green (optional, but keep it for flare)
        Color.parseColor("#00D4FF"),  // Cyan accent
        Color.parseColor("#FF1493"),  // Magenta accent
    )

    private val particles = mutableListOf<FireParticle>()
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG)
    private var animator: ValueAnimator? = null
    private var animationTime = 0f

    private val particleCount = 35

    init {
        initParticles()
    }

    private fun initParticles() {
        particles.clear()
        repeat(particleCount) {
            particles.add(createParticle())
        }
    }

    private fun createParticle(): FireParticle {
        return FireParticle(
            x = 0.5f,  // Center
            y = 0.7f,  // Start from bottom area
            radius = Random.nextFloat() * 12f + 4f,
            speedY = Random.nextFloat() * 0.008f + 0.003f,
            speedX = (Random.nextFloat() - 0.5f) * 0.004f,
            alpha = Random.nextFloat() * 0.6f + 0.4f,
            colorIndex = Random.nextInt(fireColors.size),
            phase = Random.nextFloat() * 360f,
            waveAmplitude = Random.nextFloat() * 0.03f + 0.01f,
            waveFrequency = Random.nextFloat() * 3f + 1f
        )
    }

    override fun onAttachedToWindow() {
        super.onAttachedToWindow()
        startAnimation()
    }

    override fun onDetachedFromWindow() {
        super.onDetachedFromWindow()
        stopAnimation()
    }

    fun startAnimation() {
        if (animator?.isRunning == true) return
        
        animator = ValueAnimator.ofFloat(0f, 1f).apply {
            duration = 16  // ~60fps
            repeatCount = ValueAnimator.INFINITE
            interpolator = LinearInterpolator()
            addUpdateListener {
                animationTime += 0.016f
                updateParticles()
                invalidate()
            }
            start()
        }
    }

    fun stopAnimation() {
        animator?.cancel()
        animator = null
    }

    private fun updateParticles() {
        for (particle in particles) {
            // Fluid motion using sine waves for horizontal drift
            particle.phase += 0.05f
            val drift = sin(particle.phase.toDouble()).toFloat() * particle.waveAmplitude
            
            particle.x += particle.speedX + drift * 0.1f
            particle.y -= particle.speedY * (1f + sin(particle.phase.toDouble()).toFloat() * 0.2f)
            
            // Random color shifts for "living" fire
            if (Random.nextFloat() < 0.05f) {
                particle.colorIndex = Random.nextInt(fireColors.size)
            }
            
            // Smoother fade out
            particle.alpha = ((particle.y - 0.1f) / 0.6f).coerceIn(0f, 1f)
            
            if (particle.y < 0.1f || particle.alpha <= 0f) {
                resetParticle(particle)
            }
            
            // Constrain horizontally with soft padding
            particle.x = particle.x.coerceIn(0.15f, 0.85f)
        }
    }

    private fun resetParticle(particle: FireParticle) {
        particle.x = 0.2f + Random.nextFloat() * 0.6f
        particle.y = 0.8f + Random.nextFloat() * 0.2f
        particle.radius = Random.nextFloat() * 10f + 5f
        particle.speedY = Random.nextFloat() * 0.006f + 0.002f
        particle.speedX = (Random.nextFloat() - 0.5f) * 0.003f
        particle.alpha = Random.nextFloat() * 0.5f + 0.5f
        particle.phase = Random.nextFloat() * 10f
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        
        // Disable hardware acceleration requirement for BlurMaskFilter if used, 
        // but here we use layered alpha for "bloom" instead for performance.
        
        for (particle in particles) {
            val px = particle.x * width
            val py = particle.y * height
            
            val color = fireColors[particle.colorIndex]
            val alpha = (particle.alpha * 255).toInt().coerceIn(0, 255)
            
            // Bloom Layer 1: Strong core
            paint.shader = RadialGradient(
                px, py, particle.radius * 1.5f,
                intArrayOf(
                    Color.argb(alpha, Color.red(color), Color.green(color), Color.blue(color)),
                    Color.TRANSPARENT
                ),
                null,
                Shader.TileMode.CLAMP
            )
            canvas.drawCircle(px, py, particle.radius * 1.5f, paint)
            
            // Bloom Layer 2: Soft outer glow (Bloom)
            paint.shader = RadialGradient(
                px, py, particle.radius * 4f,
                intArrayOf(
                    Color.argb(alpha / 3, Color.red(color), Color.green(color), Color.blue(color)),
                    Color.TRANSPARENT
                ),
                null,
                Shader.TileMode.CLAMP
            )
            canvas.drawCircle(px, py, particle.radius * 4f, paint)
        }
        
        paint.shader = null
    }

    private data class FireParticle(
        var x: Float,
        var y: Float,
        var radius: Float,
        var speedY: Float,
        var speedX: Float,
        var alpha: Float,
        var colorIndex: Int,
        var phase: Float,
        var waveAmplitude: Float,
        var waveFrequency: Float
    )
}
