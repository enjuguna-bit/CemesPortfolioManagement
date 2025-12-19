package com.arrears.manager.presentation.home

import androidx.compose.foundation.clickable
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.grid.GridCells
import androidx.compose.foundation.lazy.grid.LazyVerticalGrid
import androidx.compose.foundation.lazy.grid.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.*
import androidx.compose.material3.*
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp

data class HomeFeature(
    val title: String,
    val icon: ImageVector,
    val routeType: String,
    val description: String
)

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun HomeScreen(
    onNavigateToLoanProcessing: (String) -> Unit,
    onNavigateToSettings: () -> Unit,
    onLogout: () -> Unit
) {
    val features = listOf(
        HomeFeature(
            "Dormant Arrangement",
            Icons.Default.Schedule,
            "dormant",
            "Process dormant loan arrangements"
        ),
        HomeFeature(
            "Arrears Collected",
            Icons.Default.AttachMoney,
            "collected",
            "Compare SOD vs Current Arrears"
        ),
        HomeFeature(
            "Arrange Dues",
            Icons.Default.ListAlt,
            "arrange_dues",
            "Organize loan dues by officer"
        ),
        HomeFeature(
            "Arrange Arrears",
            Icons.Default.Warning,
            "arrange_arrears",
            "Arrears metrics dashboard"
        ),
        HomeFeature(
            "MTD Unpaid Dues",
            Icons.Default.TrendingDown,
            "mtd_unpaid",
            "Analyze unpaid dues risk"
        ),
        HomeFeature(
            "Branch Comparison",
            Icons.Default.Analytics,
            "branch_comparison",
            "MTD branch performance analysis"
        )
    )

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Arrears Manager") },
                actions = {
                    IconButton(onClick = onNavigateToSettings) {
                        Icon(Icons.Default.Settings, contentDescription = "Settings")
                    }
                    IconButton(onClick = onLogout) {
                        Icon(Icons.Default.ExitToApp, contentDescription = "Logout")
                    }
                }
            )
        }
    ) { padding ->
        LazyVerticalGrid(
            columns = GridCells.Fixed(2),
            contentPadding = PaddingValues(16.dp),
            horizontalArrangement = Arrangement.spacedBy(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp),
            modifier = Modifier.padding(padding)
        ) {
            items(features) { feature ->
                FeatureCard(
                    feature = feature,
                    onClick = { onNavigateToLoanProcessing(feature.routeType) }
                )
            }
        }
    }
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun FeatureCard(
    feature: HomeFeature,
    onClick: () -> Unit
) {
    Card(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth().height(160.dp),
        elevation = CardDefaults.cardElevation(defaultElevation = 4.dp)
    ) {
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            Icon(
                imageVector = feature.icon,
                contentDescription = null,
                modifier = Modifier.size(48.dp),
                tint = MaterialTheme.colorScheme.primary
            )
            Spacer(modifier = Modifier.height(8.dp))
            Text(
                text = feature.title,
                style = MaterialTheme.typography.titleMedium,
                textAlign = TextAlign.Center
            )
            Spacer(modifier = Modifier.height(4.dp))
            Text(
                text = feature.description,
                style = MaterialTheme.typography.bodySmall,
                textAlign = TextAlign.Center,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}
