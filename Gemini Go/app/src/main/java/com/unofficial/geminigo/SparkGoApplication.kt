package com.unofficial.geminigo

import android.app.Application
import android.util.Log

/**
 * Custom Application class that initializes the Safety System first.
 */
class SparkGoApplication : Application() {

    override fun onCreate() {
        super.onCreate()
        
        val safetyManager = SafetyManager.getInstance(this)
        
        // Setup Global Crash Handler
        val defaultHandler = Thread.getDefaultUncaughtExceptionHandler()
        Thread.setDefaultUncaughtExceptionHandler { thread, throwable ->
            Log.e("SparkGoApplication", "CRITICAL ERROR: ${throwable.message}")
            // Log the crash in our safety system
            safetyManager.recordCrash()
            
            // Allow default handler to proceed (app will crash normally)
            defaultHandler?.uncaughtException(thread, throwable)
        }
    }
}
