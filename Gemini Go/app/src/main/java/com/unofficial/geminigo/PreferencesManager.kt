package com.unofficial.geminigo

import android.content.Context
import android.content.SharedPreferences
import androidx.appcompat.app.AppCompatDelegate

/**
 * Manages app preferences including first launch detection and theme settings.
 */
class PreferencesManager(context: Context) {
    
    companion object {
        private const val PREFS_NAME = "spark_go_prefs"
        private const val KEY_FIRST_LAUNCH = "first_launch"
        private const val KEY_THEME_MODE = "theme_mode"
        
        const val THEME_SYSTEM = 0
        const val THEME_LIGHT = 1
        const val THEME_DARK = 2
    }
    
    private val prefs: SharedPreferences = context.getSharedPreferences(PREFS_NAME, Context.MODE_PRIVATE)
    
    /**
     * Check if this is the first launch of the app
     */
    fun isFirstLaunch(): Boolean {
        return prefs.getBoolean(KEY_FIRST_LAUNCH, true)
    }
    
    /**
     * Mark that the first launch has been completed
     */
    fun setFirstLaunchComplete() {
        prefs.edit().putBoolean(KEY_FIRST_LAUNCH, false).apply()
    }
    
    /**
     * Get the saved theme mode
     */
    fun getThemeMode(): Int {
        return prefs.getInt(KEY_THEME_MODE, THEME_SYSTEM)
    }
    
    /**
     * Save the theme mode preference
     */
    fun setThemeMode(mode: Int) {
        prefs.edit().putInt(KEY_THEME_MODE, mode).apply()
    }
    
    /**
     * Apply the saved theme mode to the app
     */
    fun applyTheme() {
        val nightMode = when (getThemeMode()) {
            THEME_LIGHT -> AppCompatDelegate.MODE_NIGHT_NO
            THEME_DARK -> AppCompatDelegate.MODE_NIGHT_YES
            else -> AppCompatDelegate.MODE_NIGHT_FOLLOW_SYSTEM
        }
        AppCompatDelegate.setDefaultNightMode(nightMode)
    }
}
