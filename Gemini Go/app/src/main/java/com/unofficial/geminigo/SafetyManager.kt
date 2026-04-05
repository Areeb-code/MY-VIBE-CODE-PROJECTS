package com.unofficial.geminigo

import android.app.ActivityManager
import android.content.Context
import android.content.Intent
import android.content.SharedPreferences
import android.os.Build
import android.util.Log

/**
 * An independent, fail-safe manager designed to monitor app health 
 * and prevent resource-related instability or boot-loops.
 */
class SafetyManager private constructor(context: Context) {

    companion object {
        private const val TAG = "SafetyManager"
        private const val PREFS_NAME = "safety_system_v1"
        private const val KEY_IS_SEIZED = "app_seized"
        private const val KEY_CRASH_COUNT = "early_crash_count"
        private const val KEY_LAST_CRASH_TIME = "last_crash_time"
        
        private const val CRASH_THRESHOLD = 3
        private const val CRASH_WINDOW_MS = 60000L // 1 minute

        @Volatile
        private var INSTANCE: SafetyManager? = null

        fun getInstance(context: Context): SafetyManager {
            return INSTANCE ?: synchronized(this) {
                INSTANCE ?: SafetyManager(context.applicationContext).also { INSTANCE = it }
            }
        }
    }

    private val prefs: SharedPreferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    private val appContext = context

    /**
     * Checks if the app is marked as "seized" due to instability or remote kill.
     */
    fun isAppSeized(): Boolean {
        return try {
            prefs.getBoolean(KEY_IS_SEIZED, false)
        } catch (e: Exception) {
            false // Fail-safe: don't block if prefs fail
        }
    }

    /**
     * Records a crash and determines if the app should be seized.
     */
    fun recordCrash() {
        try {
            val now = System.currentTimeMillis()
            val lastCrash = prefs.getLong(KEY_LAST_CRASH_TIME, 0)
            var count = prefs.getInt(KEY_CRASH_COUNT, 0)

            if (now - lastCrash < CRASH_WINDOW_MS) {
                count++
            } else {
                count = 1
            }

            val editor = prefs.edit()
            editor.putLong(KEY_LAST_CRASH_TIME, now)
            editor.putInt(KEY_CRASH_COUNT, count)

            if (count >= CRASH_THRESHOLD) {
                Log.e(TAG, "Unstable state detected! Seizing app.")
                editor.putBoolean(KEY_IS_SEIZED, true)
            }
            editor.apply()
        } catch (e: Exception) {
            // Do nothing, don't crash while recording a crash
        }
    }

    /**
     * Resets the safety state.
     */
    fun resetSafety() {
        try {
            prefs.edit()
                .putBoolean(KEY_IS_SEIZED, false)
                .putInt(KEY_CRASH_COUNT, 0)
                .apply()
        } catch (e: Exception) {}
    }

    /**
     * Checks for high-risk device conditions (e.g. extremely low RAM).
     */
    fun isLowSpecs(): Boolean {
        return try {
            val activityManager = appContext.getSystemService(Context.ACTIVITY_SERVICE) as? ActivityManager
            val memInfo = ActivityManager.MemoryInfo()
            activityManager?.getMemoryInfo(memInfo)
            
            // If total memory < 2.5GB (to be safe for 2GB devices), mark as low spec
            val lowMemoryLimit = 2500L * 1024 * 1024 
            memInfo.totalMem < lowMemoryLimit || activityManager?.isLowRamDevice == true
        } catch (e: Exception) {
            false
        }
    }

    /**
     * Redirects to the shutdown activity if app is seized.
     */
    fun checkAndRedirect(context: android.app.Activity) {
        if (isAppSeized() && context !is SafetyShutdownActivity) {
            val intent = Intent(context, SafetyShutdownActivity::class.java)
            intent.flags = Intent.FLAG_ACTIVITY_NEW_TASK or Intent.FLAG_ACTIVITY_CLEAR_TASK
            context.startActivity(intent)
            context.finish()
        }
    }
}
