# Add project specific ProGuard rules here.
# You can control the set of applied configuration files using the
# proguardFiles setting in build.gradle.
#
# For more details, see
#   http://developer.android.com/guide/developing/tools/proguard.html

# ProGuard rules for Spark Go
-keepclassmembers class * {
    @android.webkit.JavascriptInterface <methods>;
}

-keep class android.webkit.** { *; }
-keep interface android.webkit.** { *; }

-keep class com.unofficial.geminigo.MainActivity { *; }
-keep class com.unofficial.geminigo.SparkGoAssistantService { *; }
-keep class com.unofficial.geminigo.SparkGoAssistantSession { *; }
-keep class com.unofficial.geminigo.SparkGoAssistantSessionService { *; }
-keep class com.unofficial.geminigo.SparkGoRecognitionService { *; }
-keep class com.unofficial.geminigo.SparkGoApplication { *; }
-keep class com.unofficial.geminigo.SafetyManager { *; }
-keep class com.unofficial.geminigo.SafetyShutdownActivity { *; }

-dontwarn com.unofficial.geminigo.**

# Uncomment this to preserve the line number information for
# debugging stack traces.
#-keepattributes SourceFile,LineNumberTable

# If you keep the line number information, uncomment this to
# hide the original source file name.
#-renamesourcefileattribute SourceFile