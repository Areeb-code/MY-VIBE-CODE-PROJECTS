package com.unofficial.geminigo

import android.content.Intent
import android.os.Bundle
import android.speech.RecognitionService

/**
 * Recognition service required for the app to appear in Android's
 * default digital assistant settings.
 * 
 * This is a stub implementation - actual speech recognition is handled
 * by the WebView (gemini.google.com).
 */
class SparkGoRecognitionService : RecognitionService() {

    override fun onStartListening(intent: Intent?, callback: Callback?) {
        // Stub implementation - not used directly
        // Recognition is handled by the WebView
    }

    override fun onStopListening(callback: Callback?) {
        // Stub implementation
    }

    override fun onCancel(callback: Callback?) {
        // Stub implementation
    }
}
