package com.arrears.manager.presentation.loans

import android.net.Uri
import android.widget.Toast
import androidx.activity.compose.rememberLauncherForActivityResult
import androidx.activity.result.contract.ActivityResultContracts
import androidx.compose.foundation.layout.*
import androidx.compose.material.icons.Icons
import androidx.compose.material.icons.filled.ArrowBack
import androidx.compose.material.icons.filled.CheckCircle
import androidx.compose.material.icons.filled.CloudUpload
import androidx.compose.material.icons.filled.Error

import androidx.compose.material3.*
import androidx.compose.runtime.*
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.hilt.navigation.compose.hiltViewModel

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun LoanProcessingScreen(
    processingType: String,
    onNavigateBack: () -> Unit,
    viewModel: LoanProcessingViewModel = hiltViewModel()
) {
    val context = LocalContext.current
    val uriHandler = androidx.compose.ui.platform.LocalUriHandler.current
    val uploadState by viewModel.uploadState.collectAsState()
    
    // State to hold selected URIs
    var selectedFileUri by remember { mutableStateOf<Uri?>(null) }
    var selectedSodUri by remember { mutableStateOf<Uri?>(null) }
    var selectedCurUri by remember { mutableStateOf<Uri?>(null) }

    // Launchers
    val singleFileLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        selectedFileUri = uri
    }

    val sodFileLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        selectedSodUri = uri
    }
    
    val curFileLauncher = rememberLauncherForActivityResult(
        contract = ActivityResultContracts.GetContent()
    ) { uri: Uri? ->
        selectedCurUri = uri
    }
    
    // Title mapping
    val title = when (processingType) {
        "dormant" -> "Dormant Arrangement"
        "collected" -> "Arrears Collected"
        "arrange_dues" -> "Arrange Dues"
        "arrange_arrears" -> "Arrange Arrears"
        "mtd_unpaid" -> "MTD Unpaid Dues"
        else -> "Loan Processing"
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = { Text(title) },
                navigationIcon = {
                    IconButton(onClick = onNavigateBack) {
                        Icon(Icons.Default.ArrowBack, contentDescription = "Back")
                    }
                }
            )
        }
    ) { padding ->
        Column(
            modifier = Modifier
                .padding(padding)
                .fillMaxSize()
                .padding(16.dp),
            horizontalAlignment = Alignment.CenterHorizontally,
            verticalArrangement = Arrangement.Center
        ) {
            
            when (uploadState) {
                is UploadState.Loading -> {
                    CircularProgressIndicator()
                    Spacer(modifier = Modifier.height(16.dp))
                    Text("Processing...", style = MaterialTheme.typography.bodyLarge)
                }
                is UploadState.Success -> {
                    Icon(
                        Icons.Default.CheckCircle,
                        contentDescription = "Success",
                        tint = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.size(64.dp)
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    val successState = uploadState as UploadState.Success
                    Text(
                        successState.message,
                        style = MaterialTheme.typography.titleMedium,
                        textAlign = TextAlign.Center
                    )
                    
                    if (successState.downloadUrl != null) {
                        Spacer(modifier = Modifier.height(16.dp))
                        Button(
                            onClick = { 
                                try {
                                    uriHandler.openUri(successState.downloadUrl)
                                } catch (e: Exception) {
                                    Toast.makeText(context, "Could not open link", Toast.LENGTH_SHORT).show()
                                }
                            },
                            colors = ButtonDefaults.buttonColors(
                                containerColor = MaterialTheme.colorScheme.secondary
                            )
                        ) {
                            Icon(Icons.Default.CloudUpload, contentDescription = null)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text("Download Report")
                        }
                    }

                    Spacer(modifier = Modifier.height(24.dp))
                    Button(onClick = { 
                        viewModel.resetState()
                        selectedFileUri = null
                        selectedSodUri = null
                        selectedCurUri = null
                    }) {
                        Text("Process Another")
                    }
                }
                is UploadState.Error -> {
                    Icon(
                        Icons.Default.Error,
                        contentDescription = "Error",
                        tint = MaterialTheme.colorScheme.error,
                        modifier = Modifier.size(64.dp)
                    )
                    Spacer(modifier = Modifier.height(16.dp))
                    Text(
                        (uploadState as UploadState.Error).message,
                        style = MaterialTheme.typography.bodyLarge,
                        color = MaterialTheme.colorScheme.error,
                        textAlign = TextAlign.Center
                    )
                    Spacer(modifier = Modifier.height(24.dp))
                    Button(onClick = { viewModel.resetState() }) {
                        Text("Try Again")
                    }
                }
                is UploadState.Idle -> {
                    Text(
                        text = "$title Upload",
                        style = MaterialTheme.typography.headlineSmall
                    )
                    Spacer(modifier = Modifier.height(32.dp))

                    if (processingType == "collected") {
                        // Two file upload UI
                        OutlinedButton(
                            onClick = { sodFileLauncher.launch("*/*") },
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Icon(Icons.Default.CloudUpload, contentDescription = null)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(if (selectedSodUri != null) "SOD File Selected" else "Select SOD File")
                        }
                        
                        Spacer(modifier = Modifier.height(16.dp))
                        
                        OutlinedButton(
                            onClick = { curFileLauncher.launch("*/*") },
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Icon(Icons.Default.CloudUpload, contentDescription = null)
                            Spacer(modifier = Modifier.width(8.dp))
                            Text(if (selectedCurUri != null) "Current File Selected" else "Select Current File")
                        }
                        
                        Spacer(modifier = Modifier.height(32.dp))
                        
                        Button(
                            onClick = {
                                if (selectedSodUri != null && selectedCurUri != null) {
                                    viewModel.uploadTwoFiles(selectedSodUri!!, selectedCurUri!!)
                                } else {
                                    Toast.makeText(context, "Please select both files", Toast.LENGTH_SHORT).show()
                                }
                            },
                            enabled = selectedSodUri != null && selectedCurUri != null,
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text("Process Data")
                        }
                        
                    } else {
                        // Single file upload UI
                        OutlinedButton(
                            onClick = { singleFileLauncher.launch("*/*") }, // Allow all types, logic handles validation
                            modifier = Modifier.fillMaxWidth()
                        ) {
                             Icon(Icons.Default.CloudUpload, contentDescription = null)
                             Spacer(modifier = Modifier.width(8.dp))
                             Text(if (selectedFileUri != null) "File Selected" else "Select File")
                        }
                        
                        if (selectedFileUri != null) {
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                "Ready to upload", 
                                style = MaterialTheme.typography.bodySmall,
                                color = MaterialTheme.colorScheme.outline
                            )
                        }
                        
                        Spacer(modifier = Modifier.height(32.dp))
                        
                        Button(
                            onClick = { 
                                if (selectedFileUri != null) {
                                    viewModel.uploadFile(selectedFileUri!!, processingType) 
                                } else {
                                     Toast.makeText(context, "Please select a file", Toast.LENGTH_SHORT).show()
                                }
                            },
                            enabled = selectedFileUri != null,
                            modifier = Modifier.fillMaxWidth()
                        ) {
                            Text("Process Data")
                        }
                    }
                }
            }
        }
    }
}
