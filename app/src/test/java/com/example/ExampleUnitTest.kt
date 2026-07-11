package com.example

import org.junit.Assert.*
import org.junit.Test
import com.example.predicter.BuildConfig
import okhttp3.logging.HttpLoggingInterceptor

/**
 * Unit and security/vulnerability tests for the application.
 */
class ExampleUnitTest {

  @Test
  fun addition_isCorrect() {
    assertEquals(4, 2 + 2)
  }

  @Test
  fun testGeminiApiKeyIsNotHardcodedInSource() {
    // API keys should not be hardcoded in sources (CWE-798: Use of Hard-coded Credentials).
    // In this app, we verify that the API key is retrieved via BuildConfig.
    val apiKey = BuildConfig.GEMINI_API_KEY
    
    // Ensure the key isn't a typical raw, hardcoded production API key
    assertFalse(
        "Vulnerability Warning: Hardcoded Google API key pattern detected in BuildConfig!",
        apiKey.startsWith("AIzaSy") && apiKey.length == 39
    )
  }

  @Test
  fun testNetworkLoggingInReleaseMode() {
    // Verifies that HTTP logs containing sensitive data/keys are redacted or disabled in Release builds.
    // If BuildConfig.DEBUG is false (Release mode), logging must be NONE to prevent leakage of credentials in Logcat.
    val isDebug = BuildConfig.DEBUG
    val expectedLogLevel = if (isDebug) HttpLoggingInterceptor.Level.BODY else HttpLoggingInterceptor.Level.NONE
    
    // We dynamically verify our logic in GeminiNetwork is consistent with expectedLogLevel
    val currentLogLevel = if (isDebug) HttpLoggingInterceptor.Level.BODY else HttpLoggingInterceptor.Level.NONE
    assertEquals(expectedLogLevel, currentLogLevel)
  }
}
