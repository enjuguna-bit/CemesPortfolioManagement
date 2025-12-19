package com.arrears.manager.presentation.loans

import android.net.Uri
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.Download
import androidx.compose.material.icons.filled.Upload
import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import com.arrears.manager.data.model.BranchPerformance
import com.arrears.manager.data.model.MTDSummary

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun BranchComparisonScreen(
    viewModel: BranchComparisonViewModel,
    onNavigateBack: () -> Unit,
    onDownload: (String) -> Unit
) {
    val uploadState by viewModel.uploadState.collectAsState()
    val branchData by viewModel.branchData.collectAsState()
    val summary by viewModel.summary.collectAsState()
    
    var incomeFileUri by remember { mutableStateOf<Uri?>(null) }
    var crFileUri by remember { mutableStateOf<Uri?>(null) }
    var disbFileUri by remember { mutableStateOf<Uri?>(null) }
    
    val incomeFilePicker = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri -> uri?.let { incomeFileUri = it } }
    
    val crFilePicker = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri -> uri?.let { crFileUri = it } }
    
    val disbFilePicker = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri -> uri?.let { disbFileUri = it } }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text("Branch Comparison") },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, "Back")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .fillMaxSize()
                .padding(padding)
                .padding(16.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            when (uploadState) {
                is BranchUploadState.Idle -> {
                    FileSelectionSection(
                        incomeFileUri = incomeFileUri,
                        crFileUri = crFileUri,
                        disbFileUri = disbFileUri,
                        onSelectIncomeFile = { incomeFilePicker.launch("*/*") },
                        onSelectCrFile = { crFilePicker.launch("*/*") },
                        onSelectDisbFile = { disbFilePicker.launch("*/*") }
                    )
                    
                    Button(
                        onClick = {
                            if (incomeFileUri != null && crFileUri != null && disbFileUri != null) {
                                viewModel.uploadFiles(incomeFileUri!!, crFileUri!!, disbFileUri!!)
                            }
                        },
                        modifier = Modifier.fillMaxWidth(),
                        enabled = incomeFileUri != null && crFileUri != null && disbFileUri != null
                    ) {
                        Icon(Icons.Default.Upload, null, modifier = Modifier.size(20.dp))
                        Spacer(Modifier.width(8.dp))
                        Text("Upload & Analyze")
                    }
                }
                
                is BranchUploadState.Loading -> {
                    Column(
                        modifier = Modifier.fillMaxSize(),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        CircularProgressIndicator()
                        Spacer(Modifier.height(16.dp))
                        Text("Analyzing branch performance...")
                    }
                }
                
                is BranchUploadState.Success -> {
                    val state = uploadState as BranchUploadState.Success
                    ResultSection(
                        summary = summary,
                        branchData = branchData,
                        downloadUrl = state.downloadUrl,
                        onDownload = onDownload,
                        onReset = { viewModel.resetState() }
                    )
                }
                
                is BranchUploadState.Error -> {
                    Column(
                        modifier = Modifier.fillMaxSize(),
                        horizontalAlignment = Alignment.CenterHorizontally,
                        verticalArrangement = Arrangement.Center
                    ) {
                        Text(
                            text = "Error",
                            style = MaterialTheme.typography.headlineSmall,
                            color = MaterialTheme.colorScheme.error
                        )
                        Spacer(Modifier.height(8.dp))
                        Text(
                            text = (uploadState as BranchUploadState.Error).message,
                            textAlign = TextAlign.Center
                        )
                        Spacer(Modifier.height(16.dp))
                        Button(onClick = { viewModel.resetState() }) {
                            Text("Try Again")
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun FileSelectionSection(
    incomeFileUri: Uri?,
    crFileUri: Uri?,
    disbFileUri: Uri?,
    onSelectIncomeFile: () -> Unit,
    onSelectCrFile: () -> Unit,
    onSelectDisbFile: () -> Unit
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surfaceVariant
        )
    ) {
        Column(modifier = Modifier.padding(16.dp), verticalArrangement = Arrangement.spacedBy(12.dp)) {
            Text(
                "Select MTD Files",
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold
            )
            
            FilePickerButton(
                label = "MTD Income File",
                fileSelected = incomeFileUri != null,
                onClick = onSelectIncomeFile
            )
            
            FilePickerButton(
                label = "MTD CR File",
                fileSelected = crFileUri != null,
                onClick = onSelectCrFile
            )
            
            FilePickerButton(
                label = "MTD Disbursement File",
                fileSelected = disbFileUri != null,
                onClick = onSelectDisbFile
            )
        }
    }
}

@Composable
fun FilePickerButton(label: String, fileSelected: Boolean, onClick: () -> Unit) {
    OutlinedButton(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth()
    ) {
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.SpaceBetween,
            verticalAlignment = Alignment.CenterVertically
        ) {
            Text(label)
            Text(
                if (fileSelected) "✓ Selected" else "Choose File",
                color = if (fileSelected) MaterialTheme.colorScheme.primary else MaterialTheme.colorScheme.onSurface
            )
        }
    }
}

@Composable
fun ResultSection(
    summary: MTDSummary?,
    branchData: List<BranchPerformance>,
    downloadUrl: String?,
    onDownload: (String) -> Unit,
    onReset: () -> Unit
) {
    LazyColumn(
        verticalArrangement = Arrangement.spacedBy(16.dp)
    ) {
        // Summary Cards
        item {
            summary?.let {
                SummaryCards(it)
            }
        }
        
        // Download Button
        if (downloadUrl != null) {
            item {
                Button(
                    onClick = { onDownload(downloadUrl) },
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Icon(Icons.Default.Download, null)
                    Spacer(Modifier.width(8.dp))
                    Text("Download Excel Report")
                }
            }
        }
        
        // Branch Rankings
        item {
            Text(
                "Branch Rankings",
                style = MaterialTheme.typography.titleLarge,
                fontWeight = FontWeight.Bold
            )
        }
        
        items(branchData) { branch ->
            BranchCard(branch)
        }
        
        // Reset Button
        item {
            OutlinedButton(
                onClick = onReset,
                modifier = Modifier.fillMaxWidth()
            ) {
                Text("Analyze New Files")
            }
            Spacer(Modifier.height(16.dp))
        }
    }
}

@Composable
fun SummaryCards(summary: MTDSummary) {
    Column(verticalArrangement = Arrangement.spacedBy(8.dp)) {
        Text(
            "Summary Statistics",
            style = MaterialTheme.typography.titleMedium,
            fontWeight = FontWeight.Bold
        )
        
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            SummaryCard(
                title = "Total Branches",
                value = summary.totalBranches.toString(),
                modifier = Modifier.weight(1f)
            )
            SummaryCard(
                title = "Avg CR%",
                value = String.format("%.2f%%", summary.averageCR),
                modifier = Modifier.weight(1f)
            )
        }
        
        Row(
            modifier = Modifier.fillMaxWidth(),
            horizontalArrangement = Arrangement.spacedBy(8.dp)
        ) {
            SummaryCard(
                title = "Total Income",
                value = "KES ${String.format("%,.0f", summary.totalIncome)}",
                modifier = Modifier.weight(1f)
            )
            SummaryCard(
                title = "Total Disbursement",
                value = "KES ${String.format("%,.0f", summary.totalDisbursement)}",
                modifier = Modifier.weight(1f)
            )
        }
    }
}

@Composable
fun SummaryCard(title: String, value: String, modifier: Modifier = Modifier) {
    Card(
        modifier = modifier,
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.primaryContainer
        )
    ) {
        Column(
            modifier = Modifier.padding(12.dp),
            horizontalAlignment = Alignment.CenterHorizontally
        ) {
            Text(
                title,
                style = MaterialTheme.typography.bodySmall,
                color = MaterialTheme.colorScheme.onPrimaryContainer
            )
            Spacer(Modifier.height(4.dp))
            Text(
                value,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.onPrimaryContainer
            )
        }
    }
}

@Composable
fun BranchCard(branch: BranchPerformance) {
    Card(
        modifier = Modifier.fillMaxWidth()
    ) {
        Column(modifier = Modifier.padding(16.dp)) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween
            ) {
                Text(
                    "#${branch.rank} ${branch.branchName}",
                    style = MaterialTheme.typography.titleMedium,
                    fontWeight = FontWeight.Bold
                )
                Text(
                    "Score: ${String.format("%.1f", branch.performanceScore)}",
                    style = MaterialTheme.typography.titleMedium,
                    color = MaterialTheme.colorScheme.primary,
                    fontWeight = FontWeight.Bold
                )
            }
            
            Spacer(Modifier.height(8.dp))
            Divider()
            Spacer(Modifier.height(8.dp))
            
            BranchMetricRow("Income", "KES ${String.format("%,.0f", branch.income)}")
            BranchMetricRow("CR %", String.format("%.2f%%", branch.crPercentage))
            BranchMetricRow("Disbursement", "KES ${String.format("%,.0f", branch.disbursement)}")
        }
    }
}

@Composable
fun BranchMetricRow(label: String, value: String) {
    Row(
        modifier = Modifier.fillMaxWidth(),
        horizontalArrangement = Arrangement.SpaceBetween
    ) {
        Text(label, style = MaterialTheme.typography.bodyMedium)
        Text(value, style = MaterialTheme.typography.bodyMedium, fontWeight = FontWeight.SemiBold)
    }
}
