package com.unofficial.geminigo

import android.animation.ValueAnimator
import android.content.Context
import android.graphics.*
import android.util.AttributeSet
import android.view.View
import android.view.animation.LinearInterpolator
import kotlin.math.sin
import kotlin.random.Random

/**
 * Particle helper class for the fire animation.
 */
data class FireParticle(
    var x: Float,
    var y: Float,
    var radius: Float,
    var speedY: Float,
    var speedX: Float,
    var alpha: Float,
    var colorIndex: Int
)

/**
 * A modern, high-end View that renders a logo made of "living fire".
 * It uses procedural particle motion and alpha blending with logo mask.
 */
class LogoFireView @JvmOverloads constructor(
    context: Context,
    attrs: AttributeSet? = null,
    defStyleAttr: Int = 0
) : View(context, attrs, defStyleAttr) {

    private val sparkPath = Path()
    private var maxParticles = 150
    
    // Spark Go colors
    private val fireColors = intArrayOf(
        Color.parseColor("#4285F4"), // Blue
        Color.parseColor("#9B30FF"), // Purple
        Color.parseColor("#EA4335"), // Red
        Color.parseColor("#FBBC04")  // Yellow
    )

    private val particles = mutableListOf<FireParticle>()
    private val paint = Paint(Paint.ANTI_ALIAS_FLAG)
    private val maskPaint = Paint(Paint.ANTI_ALIAS_FLAG).apply {
        xfermode = PorterDuffXfermode(PorterDuff.Mode.DST_IN)
    }
    
    private var animator: ValueAnimator? = null
    private var frameTime = 0f
    
    // Off-screen buffer for masking
    private var offscreenBitmap: Bitmap? = null
    private var offscreenCanvas: Canvas? = null

    init {
        detectDeviceSpecs()
        repeat(maxParticles) {
            particles.add(createNewParticle(initial = true))
        }
    }

    private fun detectDeviceSpecs() {
        val safety = SafetyManager.getInstance(context)
        if (safety.isLowSpecs()) {
            maxParticles = 50 // Further reduced for safety on 2GB devices
        } else {
            // Also check for power save mode
            if (android.os.Build.VERSION.SDK_INT >= android.os.Build.VERSION_CODES.LOLLIPOP_MR1) {
                val powerManager = context.getSystemService(Context.POWER_SERVICE) as? android.os.PowerManager
                if (powerManager?.isPowerSaveMode == true) {
                    maxParticles = 80
                }
            }
        }
    }

    private fun createFirePath(w: Float, h: Float): Path {
        val path = Path()
        val cx = w / 2f
        val topY = h * 0.05f
        
        // Stylized modern flame path
        // Outer flame
        path.moveTo(cx, topY)
        path.cubicTo(w * 0.8f, h * 0.35f, w * 0.9f, h * 0.6f, w * 0.8f, h * 0.75f)
        path.cubicTo(w * 0.75f, h * 0.95f, w * 0.25f, h * 0.95f, w * 0.2f, h * 0.75f)
        path.cubicTo(w * 0.1f, h * 0.6f, w * 0.2f, h * 0.35f, cx, topY)
        path.close()

        // Inner flame cutout (optional for better look)
        val innerPath = Path()
        val iCx = cx
        val iBottomY = h * 0.85f
        val iTopY = h * 0.45f
        innerPath.moveTo(iCx, iTopY)
        innerPath.cubicTo(w * 0.65f, h * 0.62f, w * 0.65f, h * 0.85f, iCx, iBottomY)
        innerPath.cubicTo(w * 0.35f, h * 0.85f, w * 0.35f, h * 0.62f, iCx, iTopY)
        innerPath.close()
        
        path.addPath(innerPath)
        path.fillType = Path.FillType.EVEN_ODD
        
        return path
    }

    private fun createNewParticle(initial: Boolean = false): FireParticle {
        return FireParticle(
            x = 0.3f + Random.nextFloat() * 0.4f,
            y = if (initial) Random.nextFloat() * 0.8f + 0.1f else 0.85f,
            radius = Random.nextFloat() * 25f + 10f,
            speedY = Random.nextFloat() * 0.005f + 0.002f,
            speedX = (Random.nextFloat() - 0.5f) * 0.002f,
            alpha = Random.nextFloat() * 0.7f + 0.3f,
            colorIndex = Random.nextInt(fireColors.size)
        )
    }

    fun startAnimation() {
        if (animator?.isRunning == true) return
        animator = ValueAnimator.ofFloat(0f, 1f).apply {
            duration = 16
            repeatCount = ValueAnimator.INFINITE
            interpolator = LinearInterpolator()
            addUpdateListener {
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
            particle.y -= particle.speedY
            particle.x += particle.speedX + sin(frameTime.toDouble() * 2 + particle.x * 10).toFloat() * 0.001f
            
            // Flicker alpha
            particle.alpha *= (0.95f + Random.nextFloat() * 0.1f).coerceIn(0f, 1f)
            
            if (Random.nextFloat() < 0.03f) {
                particle.colorIndex = (particle.colorIndex + 1) % fireColors.size
            }

            if (particle.y < 0f || particle.alpha < 0.05f) {
                resetExistingParticle(particle)
            }
        }
        frameTime += 0.016f
    }

    private fun resetExistingParticle(particle: FireParticle) {
        particle.x = 0.3f + Random.nextFloat() * 0.4f
        particle.y = 0.85f + Random.nextFloat() * 0.1f
        particle.radius = Random.nextFloat() * 25f + 10f
        particle.alpha = Random.nextFloat() * 0.7f + 0.3f
        particle.colorIndex = Random.nextInt(fireColors.size)
    }

    override fun onDraw(canvas: Canvas) {
        super.onDraw(canvas)
        
        if (width <= 0 || height <= 0) return

        if (offscreenBitmap == null || offscreenBitmap?.width != width || offscreenBitmap?.height != height) {
            offscreenBitmap = Bitmap.createBitmap(width, height, Bitmap.Config.ARGB_8888)
            offscreenCanvas = Canvas(offscreenBitmap!!)
            sparkPath.set(createFirePath(width.toFloat(), height.toFloat()))
        }

        val buffer = offscreenBitmap!!
        val bufferCanvas = offscreenCanvas!!
        
        bufferCanvas.drawColor(Color.TRANSPARENT, PorterDuff.Mode.CLEAR)

        for (particle in particles) {
            val px = particle.x * width
            val py = particle.y * height
            
            val color = fireColors[particle.colorIndex]
            val alpha = (particle.alpha * 255).toInt().coerceIn(0, 255)
            
            val radRadius = particle.radius * 2
            val gradient = RadialGradient(
                px, py, radRadius,
                intArrayOf(Color.argb(alpha, Color.red(color), Color.green(color), Color.blue(color)), Color.TRANSPARENT),
                null, Shader.TileMode.CLAMP
            )
            paint.shader = gradient
            bufferCanvas.drawCircle(px, py, radRadius, paint)
        }
        paint.shader = null

        // Draw the procedural spark mask
        bufferCanvas.drawPath(sparkPath, maskPaint)

        canvas.drawBitmap(buffer, 0f, 0f, null)
    }

    override fun onAttachedToWindow() {
        super.onAttachedToWindow()
        startAnimation()
    }

    override fun onDetachedFromWindow() {
        super.onDetachedFromWindow()
        stopAnimation()
    }
}
