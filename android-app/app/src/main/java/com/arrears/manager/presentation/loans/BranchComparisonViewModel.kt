package com.arrears.manager.presentation.loans

import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.arrears.manager.data.model.BranchPerformance
import com.arrears.manager.data.model.MTDSummary
import com.arrears.manager.data.repository.LoanRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed class BranchUploadState {
    object Idle : BranchUploadState()
    object Loading : BranchUploadState()
    data class Success(val message: String, val downloadUrl: String?) : BranchUploadState()
    data class Error(val message: String) : BranchUploadState()
}

@HiltViewModel
class BranchComparisonViewModel @Inject constructor(
    private val repository: LoanRepository
) : ViewModel() {

    private val _uploadState = MutableStateFlow<BranchUploadState>(BranchUploadState.Idle)
    val uploadState: StateFlow<BranchUploadState> = _uploadState.asStateFlow()
    
    private val _branchData = MutableStateFlow<List<BranchPerformance>>(emptyList())
    val branchData: StateFlow<List<BranchPerformance>> = _branchData.asStateFlow()
    
    private val _summary = MutableStateFlow<MTDSummary?>(null)
    val summary: StateFlow<MTDSummary?> = _summary.asStateFlow()

    fun resetState() {
        _uploadState.value = BranchUploadState.Idle
        _branchData.value = emptyList()
        _summary.value = null
    }

    fun uploadFiles(incomeUri: Uri, crUri: Uri, disbUri: Uri) {
        viewModelScope.launch {
            _uploadState.value = BranchUploadState.Loading
            
            val result = repository.processMTDParameters(incomeUri, crUri, disbUri)
            
            result.fold(
                onSuccess = { response ->
                    _summary.value = response.summary
                    _branchData.value = response.data
                    _uploadState.value = BranchUploadState.Success(
                        "Analysis complete! ${response.data.size} branches processed",
                        null // Will be added when we handle download_url from response
                    )
                },
                onFailure = { error ->
                    _uploadState.value = BranchUploadState.Error(
                        error.message ?: "Failed to process MTD parameters"
                    )
                }
            )
        }
    }
}
