package com.unofficial.geminigo

import android.service.voice.VoiceInteractionService

/**
 * Spark Go Voice Interaction Service.
 * Entry point for the assistant functionality.
 * This service makes the app appear in Android's assistant settings.
 */
class SparkGoAssistantService : VoiceInteractionService() {
    
    override fun onReady() {
        super.onReady()
        // Service is ready to handle voice interactions
    }
}
