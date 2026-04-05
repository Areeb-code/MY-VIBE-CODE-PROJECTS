package com.unofficial.geminigo

import android.Manifest
import android.animation.ObjectAnimator
import android.animation.ValueAnimator
import android.annotation.SuppressLint
import android.content.Context
import android.content.pm.PackageManager
import android.net.ConnectivityManager
import android.net.Network
import android.net.NetworkCapabilities
import android.net.NetworkRequest
import android.os.Build
import android.os.Bundle
import android.view.View
import android.view.animation.AccelerateDecelerateInterpolator
import android.view.animation.LinearInterpolator
import android.webkit.PermissionRequest
import android.webkit.WebChromeClient
import android.webkit.WebResourceError
import android.webkit.WebResourceRequest
import android.webkit.WebView
import android.webkit.WebViewClient
import android.widget.Toast
import androidx.activity.OnBackPressedCallback
import androidx.appcompat.app.AppCompatActivity
import androidx.core.app.ActivityCompat
import androidx.core.content.ContextCompat
import androidx.core.view.isVisible

class MainActivity : AppCompatActivity() {
    private lateinit var webView: WebView
    private lateinit var offlineView: View
    private lateinit var logoFireView: LogoFireView
    private lateinit var reloadButton: View
    private lateinit var connectivityManager: ConnectivityManager
    private lateinit var networkCallback: ConnectivityManager.NetworkCallback

    companion object {
        private const val PERMISSION_REQUEST_ALL = 1001
        
        private const val REBRAND_SCRIPT = """
            (function() {
                var style = document.createElement('style');
                style.textContent = `
                    img[alt*="Gemini"], 
                    img[src*="gemini"],
                    [class*="gemini-logo"],
                    [class*="GeminiLogo"],
                    svg[class*="assistant"],
                    .google-logo, .gemini-icon {
                        display: none !important;
                        visibility: hidden !important;
                    }
                `;
                document.head.appendChild(style);
                
                function replaceText(node) {
                    if (node.nodeType === Node.TEXT_NODE) {
                        var text = node.nodeValue;
                        if (text && (text.includes('Gemini') || text.includes('Bard'))) {
                            text = text.replace(/Gemini Advanced/gi, 'Spark Go Pro')
                                      .replace(/Gemini Ultra/gi, 'Spark Go Ultra')
                                      .replace(/Gemini Pro/gi, 'Spark Go')
                                      .replace(/Gemini/gi, 'Spark Go')
                                      .replace(/Bard/gi, 'Spark Go');
                            node.nodeValue = text;
                        }
                    } else if (node.nodeType === Node.ELEMENT_NODE) {
                        if (node.placeholder && (node.placeholder.includes('Gemini') || node.placeholder.includes('Bard'))) {
                            node.placeholder = node.placeholder.replace(/Ask Gemini/gi, 'Ask Gemini via Spark Go')
                                                              .replace(/Gemini/gi, 'Spark Go')
                                                              .replace(/Bard/gi, 'Spark Go');
                        }
                        const label = node.getAttribute('aria-label');
                        if (label && (label.includes('Gemini') || label.includes('Bard'))) {
                            node.setAttribute('aria-label', label.replace(/Ask Gemini/gi, 'Ask Gemini via Spark Go').replace(/Gemini/gi, 'Spark Go').replace(/Bard/gi, 'Spark Go'));
                        }

                        if (node.tagName !== 'SCRIPT' && node.tagName !== 'STYLE') {
                            for (var i = 0; i < node.childNodes.length; i++) {
                                replaceText(node.childNodes[i]);
                            }
                        }
                    }
                }
                
                replaceText(document.body);
                var observer = new MutationObserver((mutations) => {
                    mutations.forEach((mutation) => {
                        mutation.addedNodes.forEach((node) => replaceText(node));
                    });
                });
                observer.observe(document.body, { childList: true, subtree: true });
                
                if (document.title.toLowerCase().includes('gemini')) {
                    document.title = document.title.replace(/Gemini/gi, 'Spark Go');
                }
            })();
        """
    }

    override fun onCreate(savedInstanceState: Bundle?) {
        super.onCreate(savedInstanceState)
        SafetyManager.getInstance(this).checkAndRedirect(this)
        
        PreferencesManager(this).applyTheme()
        setContentView(R.layout.activity_main)

        webView = findViewById(R.id.webView)
        offlineView = findViewById(R.id.offlineView)
        logoFireView = findViewById(R.id.logoFireView)
        reloadButton = findViewById(R.id.reloadButton)

        setupWebView()
        setupBackNavigation()
        setupNetworkMonitoring()
        setupReloadButton()
        checkPermissions()
        handleIntent()
    }

    override fun onDestroy() {
        super.onDestroy()
        unregisterNetworkCallback()
    }

    private fun handleIntent() {
        if (intent?.getBooleanExtra("ACTION_VOICE_SEARCH", false) == true) {
            // Give extra time for page to load then click mic if possible
            webView.postDelayed({
                webView.evaluateJavascript("(function() { " +
                        "var selectors = ['button[aria-label*=\"mic\"]', '[class*=\"mic\"]', 'svg[class*=\"mic\"]'];" +
                        "for (var selector of selectors) {" +
                        "  var el = document.querySelector(selector);" +
                        "  if (el) {" +
                        "    while (el && el.tagName !== 'BUTTON' && el.parentElement) el = el.parentElement;" +
                        "    if (el) { el.click(); return; }" +
                        "  }" +
                        "}" +
                        "})();", null)
            }, 1500) // Reduced delay for faster response
        }
    }

    private fun checkPermissions() {
        val permissions = mutableListOf(Manifest.permission.RECORD_AUDIO)
        if (Build.VERSION.SDK_INT <= Build.VERSION_CODES.Q) {
            permissions.add(Manifest.permission.READ_EXTERNAL_STORAGE)
            permissions.add(Manifest.permission.WRITE_EXTERNAL_STORAGE)
        } else {
             permissions.add(Manifest.permission.READ_EXTERNAL_STORAGE)
        }
        permissions.add(Manifest.permission.CAMERA)

        val listToRequest = permissions.filter { 
            ContextCompat.checkSelfPermission(this, it) != PackageManager.PERMISSION_GRANTED 
        }

        if (listToRequest.isNotEmpty()) {
            ActivityCompat.requestPermissions(this, listToRequest.toTypedArray(), PERMISSION_REQUEST_ALL)
        }
    }

    override fun onRequestPermissionsResult(requestCode: Int, permissions: Array<out String>, grantResults: IntArray) {
        super.onRequestPermissionsResult(requestCode, permissions, grantResults)
        if (requestCode == PERMISSION_REQUEST_ALL) {
            if (grantResults.isNotEmpty() && grantResults.all { it == PackageManager.PERMISSION_GRANTED }) {
                webView.reload()
            } else {
                Toast.makeText(this, "Permissions are needed for full functionality", Toast.LENGTH_SHORT).show()
            }
        }
    }

    @SuppressLint("SetJavaScriptEnabled")
    private fun setupWebView() {
        webView.apply {
            settings.javaScriptEnabled = true
            settings.domStorageEnabled = true
            settings.databaseEnabled = true
            settings.displayZoomControls = false
            settings.loadWithOverviewMode = true
            settings.useWideViewPort = true
            settings.mediaPlaybackRequiresUserGesture = false
            
            // Disable pinch to zoom
            settings.setSupportZoom(false)
            settings.builtInZoomControls = false
            
            settings.userAgentString = settings.userAgentString.replace("; wv)", ")")

            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.LOLLIPOP) {
                settings.mixedContentMode = android.webkit.WebSettings.MIXED_CONTENT_ALWAYS_ALLOW
            }

            webViewClient = object : WebViewClient() {
                override fun onReceivedError(view: WebView?, request: WebResourceRequest?, error: WebResourceError?) {
                    if (request?.isForMainFrame == true) runOnUiThread { showOfflineView() }
                }
                override fun onPageFinished(view: WebView?, url: String?) {
                    super.onPageFinished(view, url)
                    view?.evaluateJavascript(REBRAND_SCRIPT, null)
                }
            }
            
            webChromeClient = object : WebChromeClient() {
                override fun onPermissionRequest(request: PermissionRequest?) {
                    val resources = request?.resources ?: return
                    for (resource in resources) {
                        if (resource == PermissionRequest.RESOURCE_AUDIO_CAPTURE || 
                            resource == PermissionRequest.RESOURCE_VIDEO_CAPTURE) {
                            runOnUiThread { request.grant(arrayOf(resource)) }
                        }
                    }
                }
            }
        }
    }

    private fun setupBackNavigation() {
        onBackPressedDispatcher.addCallback(this, object : OnBackPressedCallback(true) {
            override fun handleOnBackPressed() {
                if (webView.canGoBack() && webView.isVisible) webView.goBack()
                else { isEnabled = false; onBackPressedDispatcher.onBackPressed() }
            }
        })
    }

    private fun setupReloadButton() {
        reloadButton.setOnClickListener {
            if (isNetworkAvailable()) {
                showWebView()
                webView.loadUrl("https://gemini.google.com")
            } else {
                Toast.makeText(this, "Still no internet connection", Toast.LENGTH_SHORT).show()
            }
        }
    }

    private fun setupNetworkMonitoring() {
        connectivityManager = getSystemService(Context.CONNECTIVITY_SERVICE) as ConnectivityManager
        networkCallback = object : ConnectivityManager.NetworkCallback() {
            override fun onAvailable(network: Network) {
                runOnUiThread {
                    showWebView()
                    if (webView.url == null || webView.url == "about:blank") webView.loadUrl("https://gemini.google.com")
                    else webView.reload()
                }
            }
            override fun onLost(network: Network) {
                runOnUiThread { showOfflineView() }
            }
        }
        connectivityManager.registerNetworkCallback(NetworkRequest.Builder().addCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET).build(), networkCallback)
        if (isNetworkAvailable()) { showWebView(); webView.loadUrl("https://gemini.google.com") }
        else showOfflineView()
    }

    private fun unregisterNetworkCallback() {
        try { connectivityManager.unregisterNetworkCallback(networkCallback) } catch (e: Exception) {}
    }

    private fun isNetworkAvailable(): Boolean {
        val network = connectivityManager.activeNetwork ?: return false
        return connectivityManager.getNetworkCapabilities(network)?.hasCapability(NetworkCapabilities.NET_CAPABILITY_INTERNET) == true
    }

    private fun showWebView() {
        if (!webView.isVisible) {
            webView.isVisible = true
            offlineView.isVisible = false
            logoFireView.stopAnimation()
        }
    }

    private fun showOfflineView() {
        if (!offlineView.isVisible) {
            webView.isVisible = false
            offlineView.isVisible = true
            logoFireView.startAnimation()
            startLogoEffects()
        }
    }

    private fun startLogoEffects() {
        logoFireView.alpha = 0f
        logoFireView.scaleX = 0.8f
        logoFireView.scaleY = 0.8f
        
        logoFireView.animate()
            .alpha(1f)
            .scaleX(1.05f)
            .scaleY(1.05f)
            .setDuration(1000)
            .setInterpolator(AccelerateDecelerateInterpolator())
            .withEndAction {
                ObjectAnimator.ofFloat(logoFireView, "scaleX", 1.05f, 1f, 1.05f).apply {
                    duration = 3000
                    repeatCount = ValueAnimator.INFINITE
                    interpolator = AccelerateDecelerateInterpolator()
                    start()
                }
                ObjectAnimator.ofFloat(logoFireView, "scaleY", 1.05f, 1f, 1.05f).apply {
                    duration = 3000
                    repeatCount = ValueAnimator.INFINITE
                    interpolator = AccelerateDecelerateInterpolator()
                    start()
                }
            }
            .start()
            
        // Subtile flicker alpha for "cool" effect
        ObjectAnimator.ofFloat(logoFireView, "alpha", 0.95f, 1f, 0.95f).apply {
            duration = 100
            repeatCount = ValueAnimator.INFINITE
            interpolator = LinearInterpolator()
            start()
        }
    }
}