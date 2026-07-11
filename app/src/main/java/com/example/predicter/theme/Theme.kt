package com.example.predicter.theme

import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.darkColorScheme
import androidx.compose.material3.Typography
import androidx.compose.runtime.Composable
import androidx.compose.ui.graphics.Color

val KalshiPrimary = Color(0xFF00FF88)
val KalshiSecondary = Color(0xFF58A6FF)
val KalshiBackground = Color(0xFF0D0F12)
val KalshiSurface = Color(0xFF161A20)
val KalshiTextPrimary = Color(0xFFFFFFFF)
val KalshiError = Color(0xFFFF4466)
val KalshiWarning = Color(0xFFFFAA00)

private val CosmicColorScheme = darkColorScheme(
    primary = KalshiPrimary,
    secondary = KalshiSecondary,
    background = KalshiBackground,
    surface = KalshiSurface,
    onPrimary = KalshiTextPrimary,
    onSecondary = KalshiTextPrimary,
    onBackground = KalshiTextPrimary,
    onSurface = KalshiTextPrimary,
    error = KalshiError
)

@Composable
fun PredicterTheme(
    content: @Composable () -> Unit
) {
    MaterialTheme(
        colorScheme = CosmicColorScheme,
        typography = Typography(),
        content = content
    )
}
