package com.arrears.manager.presentation

import android.os.Bundle
import androidx.activity.ComponentActivity
import androidx.activity.compose.setContent
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Surface
import androidx.compose.ui.Modifier
import androidx.core.splashscreen.SplashScreen.Companion.installSplashScreen
import com.arrears.manager.presentation.navigation.ArrearsNavHost
import com.arrears.manager.ui.theme.ArrearsManagerTheme
import dagger.hilt.android.AndroidEntryPoint

@AndroidEntryPoint
class MainActivity : ComponentActivity() {
    
    override fun onCreate(savedInstanceState: Bundle?) {
        // Install splash screen
        installSplashScreen()
        
        super.onCreate(savedInstanceState)
        
        setContent {
            ArrearsManagerTheme {
                Surface(
                    modifier = Modifier.fillMaxSize(),
                    color = MaterialTheme.colorScheme.background
                ) {
                    ArrearsNavHost()
                }
            }
        }
    }
}
