package com.arrears.manager.ui.theme

import android.app.Activity
import android.os.Build
import androidx.compose.foundation.isSystemInDarkTheme
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.runtime.SideEffect
import androidx.compose.ui.graphics.Color
import androidx.compose.ui.graphics.toArgb
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.platform.LocalView
import androidx.core.view.WindowCompat

private val DarkColorScheme = darkColorScheme(
    primary = Primary,
    onPrimary = Color.White,
    primaryContainer = PrimaryVariant,
    onPrimaryContainer = Color.White,
    secondary = Secondary,
    onSecondary = Color.White,
    secondaryContainer = SecondaryVariant,
    onSecondaryContainer = Color.White,
    tertiary = ChartColor3,
    onTertiary = Color.White,
    error = Error,
    onError = Color.White,
    errorContainer = Color(0xFF93000A),
    onErrorContainer = Color(0xFFFFDAD6),
    background = BackgroundDark,
    onBackground = TextPrimaryDark,
    surface = SurfaceDark,
    onSurface = TextPrimaryDark,
    surfaceVariant = Color(0xFF334155),
    onSurfaceVariant = TextSecondaryDark,
    outline = Color(0xFF475569)
)

private val LightColorScheme = lightColorScheme(
    primary = Primary,
    onPrimary = Color.White,
    primaryContainer = Color(0xFFE0E7FF),
    onPrimaryContainer = Color(0xFF1E1B4B),
    secondary = Secondary,
    onSecondary = Color.White,
    secondaryContainer = Color(0xFFF3E8FF),
    onSecondaryContainer = Color(0xFF2E1065),
    tertiary = ChartColor3,
    onTertiary = Color.White,
    error = Error,
    onError = Color.White,
    errorContainer = Color(0xFFFFDAD6),
    onErrorContainer = Color(0xFF410002),
    background = BackgroundLight,
    onBackground = TextPrimaryLight,
    surface = SurfaceLight,
    onSurface = TextPrimaryLight,
    surfaceVariant = Color(0xFFF1F5F9),
    onSurfaceVariant = TextSecondaryLight,
    outline = Color(0xFFCBD5E1)
)

@Composable
fun ArrearsManagerTheme(
    darkTheme: Boolean = isSystemInDarkTheme(),
    // Dynamic color is available on Android 12+
    dynamicColor: Boolean = true,
    content: @Composable () -> Unit
) {
    val colorScheme = when {
        dynamicColor && Build.VERSION.SDK_INT >= Build.VERSION_CODES.S -> {
            val context = LocalContext.current
            if (darkTheme) dynamicDarkColorScheme(context) else dynamicLightColorScheme(context)
        }
        darkTheme -> DarkColorScheme
        else -> LightColorScheme
    }
    
    val view = LocalView.current
    if (!view.isInEditMode) {
        SideEffect {
            val window = (view.context as Activity).window
            window.statusBarColor = colorScheme.background.toArgb()
            WindowCompat.getInsetsController(window, view).isAppearanceLightStatusBars = !darkTheme
        }
    }

    MaterialTheme(
        colorScheme = colorScheme,
        typography = Typography,
        content = content
    )
}
