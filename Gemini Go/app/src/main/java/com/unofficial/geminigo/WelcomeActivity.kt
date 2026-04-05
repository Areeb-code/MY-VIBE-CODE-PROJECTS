package com.unofficial.geminigo

import android.content.Intent
import android.os.Bundle
import android.view.View
import android.view.animation.OvershootInterpolator
import androidx.appcompat.app.AppCompatActivity

/**
 * Welcome screen shown on first app launch.
 * Shows "Welcome to Spark Go" message with animated fire logo.
 */
class WelcomeActivity : AppCompatActivity() {

    private lateinit var preferencesManager: PreferencesManager
    private lateinit var logoFireView: LogoFireView
    private lateinit var getStartedButton: View

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        SafetyManager.getInstance(this).checkAndRedirect(this)
        
        preferencesManager = PreferencesManager(this)
        preferencesManager.applyTheme()
        
        if (!preferencesManager.isFirstLaunch()) {
            navigateToMain()
            return
        }
        
        setContentView(R.layout.activity_welcome)
        
        logoFireView = findViewById(R.id.logoFireView)
        getStartedButton = findViewById(R.id.getStartedButton)
        
        setupClickListeners()
        startAnimations()
    }
    
    override fun onResume() {
        super.onResume()
        logoFireView.startAnimation()
    }
    
    override fun onPause() {
        super.onPause()
        logoFireView.stopAnimation()
    }
    
    private fun setupClickListeners() {
        getStartedButton.setOnClickListener {
            preferencesManager.setFirstLaunchComplete()
            navigateToMain()
        }
    }
    
    private fun navigateToMain() {
        val intent = Intent(this, MainActivity::class.java)
        startActivity(intent)
        finish()
    }
    
    private fun startAnimations() {
        // Logo entrance animation
        logoFireView.alpha = 0f
        logoFireView.scaleX = 0.5f
        logoFireView.scaleY = 0.5f
        
        logoFireView.animate()
            .alpha(1f)
            .scaleX(1.1f) // Slight overshoot for "cool" factor
            .scaleY(1.1f)
            .setDuration(1200)
            .setInterpolator(android.view.animation.OvershootInterpolator(1.5f))
            .withEndAction {
                // Smooth breathing scale loop
                logoFireView.animate()
                    .scaleX(1.0f)
                    .scaleY(1.0f)
                    .setDuration(2000)
                    .setInterpolator(android.view.animation.AccelerateDecelerateInterpolator())
                    .setListener(null)
                    .start()
            }
            .start()
        
        logoFireView.startAnimation()
        
        // Button fade in
        getStartedButton.alpha = 0f
        getStartedButton.postDelayed({
            getStartedButton.animate()
                .alpha(1f)
                .setDuration(800)
                .start()
        }, 800)
    }
}
