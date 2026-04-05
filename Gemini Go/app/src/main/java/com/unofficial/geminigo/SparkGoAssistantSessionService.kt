package com.unofficial.geminigo

import android.os.Bundle
import android.service.voice.VoiceInteractionSession
import android.service.voice.VoiceInteractionSessionService

/**
 * Session service for Spark Go assistant interactions.
 */
class SparkGoAssistantSessionService : VoiceInteractionSessionService() {
    override fun onNewSession(args: Bundle?): VoiceInteractionSession {
        return SparkGoAssistantSession(this)
    }
}
