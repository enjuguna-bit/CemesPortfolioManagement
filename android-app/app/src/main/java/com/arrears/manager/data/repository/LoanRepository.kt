package com.arrears.manager.data.repository

import android.content.Context
import android.net.Uri
import android.provider.OpenableColumns
import com.arrears.manager.data.api.ArrearsApiService
import com.arrears.manager.data.model.LoanProcessingResponse
import com.arrears.manager.data.model.ArrearsCollectedResponse
import com.arrears.manager.data.model.MTDParametersResponse
import dagger.hilt.android.qualifiers.ApplicationContext
import okhttp3.MediaType.Companion.toMediaTypeOrNull
import okhttp3.MultipartBody
import okhttp3.RequestBody.Companion.asRequestBody
import timber.log.Timber
import java.io.File
import java.io.FileOutputStream
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class LoanRepository @Inject constructor(
    private val apiService: ArrearsApiService,
    @ApplicationContext private val context: Context
) {

    private fun prepareFilePart(partName: String, fileUri: Uri): MultipartBody.Part {
        val file = getFileFromUri(fileUri)
        val requestFile = file.asRequestBody("multipart/form-data".toMediaTypeOrNull())
        return MultipartBody.Part.createFormData(partName, file.name, requestFile)
    }

    private fun getFileFromUri(uri: Uri): File {
        val returnCursor = context.contentResolver.query(uri, null, null, null, null)
        val nameIndex = returnCursor!!.getColumnIndex(OpenableColumns.DISPLAY_NAME)
        returnCursor.moveToFirst()
        val name = returnCursor.getString(nameIndex)
        returnCursor.close()
        
        val file = File(context.cacheDir, name)
        val inputStream = context.contentResolver.openInputStream(uri)
        val outputStream = FileOutputStream(file)
        inputStream!!.copyTo(outputStream)
        
        inputStream.close()
        outputStream.close()
        
        return file
    }

    suspend fun processDormantArrangement(fileUri: Uri): Result<LoanProcessingResponse> {
        return try {
            val filePart = prepareFilePart("file", fileUri)
            val response = apiService.processDormantArrangement(filePart)
            if (response.isSuccessful && response.body() != null && response.body()!!.success) {
                Result.success(response.body()!!.data)
            } else {
                val errorMsg = response.body()?.message ?: response.message()
                Result.failure(Exception(errorMsg))
            }
        } catch (e: Exception) {
            Timber.e(e)
            Result.failure(e)
        }
    }

    suspend fun processArrearsCollected(sodUri: Uri, curUri: Uri): Result<ArrearsCollectedResponse> {
        return try {
            val sodPart = prepareFilePart("sod_file", sodUri)
            val curPart = prepareFilePart("current_file", curUri)
            val response = apiService.processArrearsCollected(sodPart, curPart)
             if (response.isSuccessful && response.body() != null && response.body()!!.success) {
                Result.success(response.body()!!.data)
            } else {
                val errorMsg = response.body()?.message ?: response.message()
                Result.failure(Exception(errorMsg))
            }
        } catch (e: Exception) {
             Timber.e(e)
            Result.failure(e)
        }
    }
    
    suspend fun processArrangeDues(fileUri: Uri): Result<LoanProcessingResponse> {
        return try {
            val filePart = prepareFilePart("file", fileUri)
            val response = apiService.processArrangeDues(filePart)
            if (response.isSuccessful && response.body() != null && response.body()!!.success) {
                Result.success(response.body()!!.data)
            } else {
                val errorMsg = response.body()?.message ?: response.message()
                Result.failure(Exception(errorMsg))
            }
        } catch (e: Exception) {
             Timber.e(e)
            Result.failure(e)
        }
    }

    suspend fun processArrangeArrears(fileUri: Uri): Result<LoanProcessingResponse> {
        return try {
            val filePart = prepareFilePart("file", fileUri)
            val response = apiService.processArrangeArrears(filePart)
            if (response.isSuccessful && response.body() != null && response.body()!!.success) {
                Result.success(response.body()!!.data)
            } else {
                val errorMsg = response.body()?.message ?: response.message()
                Result.failure(Exception(errorMsg))
            }
        } catch (e: Exception) {
             Timber.e(e)
            Result.failure(e)
        }
    }

    suspend fun processMTDUnpaidDues(fileUri: Uri): Result<LoanProcessingResponse> {
        return try {
            val filePart = prepareFilePart("file", fileUri)
            val response = apiService.processMTDUnpaidDues(filePart)
            if (response.isSuccessful && response.body() != null && response.body()!!.success) {
                Result.success(response.body()!!.data)
            } else {
                val errorMsg = response.body()?.message ?: response.message()
                Result.failure(Exception(errorMsg))
            }
        } catch (e: Exception) {
             Timber.e(e)
            Result.failure(e)
        }
    }
    
    suspend fun processMTDParameters(
        incomeUri: Uri,
        crUri: Uri,
        disbUri: Uri
    ): Result<MTDParametersResponse> {
        return try {
            val incomePart = prepareFilePart("income_file", incomeUri)
            val crPart = prepareFilePart("cr_file", crUri)
            val disbPart = prepareFilePart("disb_file", disbUri)
            
            val response = apiService.processMTDParameters(incomePart, crPart, disbPart)
            
            if (response.isSuccessful && response.body() != null && response.body()!!.success) {
                Result.success(response.body()!!.data)
            } else {
                val errorMsg = response.body()?.message ?: response.message()
                Result.failure(Exception(errorMsg))
            }
        } catch (e: Exception) {
            Timber.e(e)
            Result.failure(e)
        }
    }
}
