package com.arrears.manager.presentation.settings

import androidx.compose.foundation.layout.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Modifier

@Composable
fun SettingsScreen(
    onNavigateBack: () -> Unit
) {
    Scaffold(
        topBar = {
            SmallTopAppBar(title = { Text("Settings") })
        }
    ) { padding ->
        Box(modifier = Modifier.padding(padding)) {
            Text("Settings Screen - TODO")
        }
    }
}
