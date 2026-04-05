package com.unofficial.geminigo

import android.os.Bundle
import android.widget.Button
import android.widget.TextView
import androidx.appcompat.app.AppCompatActivity

/**
 * A minimal, robust Activity that takes over when the app is "seized" due to instability.
 * It has zero dependencies on custom views or complex logic.
 */
class SafetyShutdownActivity : AppCompatActivity() {

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        
        // Simple programmatic layout to stay independent of layout inflation if needed, 
        // but a simple XML is usually fine too. Let's use simple logic.
        val container = android.widget.LinearLayout(this)
        container.orientation = android.widget.LinearLayout.VERTICAL
        container.gravity = android.view.Gravity.CENTER
        container.setPadding(64, 64, 64, 64)
        container.setBackgroundColor(android.graphics.Color.WHITE)

        val title = TextView(this)
        title.text = "Safety Mode Active"
        title.textSize = 24f
        title.setTextColor(android.graphics.Color.RED)
        title.setTypeface(null, android.graphics.Typeface.BOLD)
        container.addView(title)

        val message = TextView(this)
        message.text = "\nSpark Go has been temporarily disabled to prevent device instability (too many crashes or resource overload).\n"
        message.textSize = 16f
        message.setTextColor(android.graphics.Color.BLACK)
        container.addView(message)

        val btnReset = Button(this)
        btnReset.text = "Try to Reset & Restart"
        btnReset.setOnClickListener {
            SafetyManager.getInstance(this).resetSafety()
            // Clear identity to trigger a clean start
            getSharedPreferences("spark_go_prefs", 0).edit().clear().apply()
            
            val intent = Intent(this, WelcomeActivity::class.java)
            intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
            startActivity(intent)
            finish()
        }
        container.addView(btnReset)

        setContentView(container)
    }
}

// Extension to allow Intent usage inside the Activity
private typealias Intent = android.content.Intent
