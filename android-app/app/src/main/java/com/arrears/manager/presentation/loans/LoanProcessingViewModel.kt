package com.arrears.manager.presentation.loans

import android.net.Uri
import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.arrears.manager.data.repository.LoanRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.MutableStateFlow
import kotlinx.coroutines.flow.StateFlow
import kotlinx.coroutines.flow.asStateFlow
import kotlinx.coroutines.launch
import javax.inject.Inject

sealed class UploadState {
    object Idle : UploadState()
    object Loading : UploadState()
    data class Success(val message: String, val downloadUrl: String? = null) : UploadState()
    data class Error(val message: String) : UploadState()
}

@HiltViewModel
class LoanProcessingViewModel @Inject constructor(
    private val repository: LoanRepository
) : ViewModel() {

    private val _uploadState = MutableStateFlow<UploadState>(UploadState.Idle)
    val uploadState: StateFlow<UploadState> = _uploadState.asStateFlow()

    fun resetState() {
        _uploadState.value = UploadState.Idle
    }

    fun uploadFile(uri: Uri, type: String) {
        viewModelScope.launch {
            _uploadState.value = UploadState.Loading
            
            val result = when (type) {
                "dormant" -> repository.processDormantArrangement(uri)
                "arrange_dues" -> repository.processArrangeDues(uri)
                "arrange_arrears" -> repository.processArrangeArrears(uri)
                "mtd_unpaid" -> repository.processMTDUnpaidDues(uri)
                else -> Result.failure(Exception("Unknown processing type: $type"))
            }

            result.fold(
                onSuccess = { response -> 
                    _uploadState.value = UploadState.Success(
                        "Processed successfully!", 
                        response.downloadUrl
                    ) 
                },
                onFailure = { error -> 
                    _uploadState.value = UploadState.Error(error.message ?: "Upload failed") 
                }
            )
        }
    }

    fun uploadTwoFiles(sodUri: Uri, curUri: Uri) {
        viewModelScope.launch {
             _uploadState.value = UploadState.Loading
             val result = repository.processArrearsCollected(sodUri, curUri)
             
             result.fold(
                onSuccess = { response ->
                    _uploadState.value = UploadState.Success(
                        "Arrears Collected Processed!",
                        response.downloadUrl
                    ) 
                },
                onFailure = { error -> 
                    _uploadState.value = UploadState.Error(error.message ?: "Upload failed") 
                }
            )
        }
    }
}
