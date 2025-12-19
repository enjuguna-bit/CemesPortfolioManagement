package com.arrears.manager.data.repository

import android.content.Context
import android.provider.Settings
import com.arrears.manager.data.api.ArrearsApiService
import com.arrears.manager.data.model.AuthData
import com.arrears.manager.data.model.LoginRequest
import dagger.hilt.android.qualifiers.ApplicationContext
import kotlinx.coroutines.flow.Flow
import kotlinx.coroutines.flow.flow
import timber.log.Timber
import javax.inject.Inject
import javax.inject.Singleton

@Singleton
class AuthRepository @Inject constructor(
    private val apiService: ArrearsApiService,
    @ApplicationContext private val context: Context
) {
    val isLoggedIn: Flow<Boolean> = flow {
        // TODO: Check if token exists in DataStore
        emit(false)
    }

    suspend fun login(username: String, password: String): Result<AuthData> {
        return try {
            val deviceId = Settings.Secure.getString(
                context.contentResolver,
                Settings.Secure.ANDROID_ID
            ) ?: "unknown-device"
            
            Timber.d("Attempting login for user: $username with device: $deviceId")
            
            val response = apiService.login(
                LoginRequest(
                    username = username,
                    password = password
                )
            )
            
            Timber.d("Login response code: ${response.code()}")
            
            if (response.isSuccessful && response.body() != null) {
                val apiResponse = response.body()!!
                
                if (apiResponse.success && apiResponse.data != null) {
                    Timber.i("Login successful for user: ${apiResponse.data.user.username}")
                    // TODO: Save tokens to DataStore
                    // TODO: Save device ID and user info
                    Result.success(apiResponse.data)
                } else {
                    val errorMsg = apiResponse.message ?: "Login failed: Unknown error"
                    Timber.e("Login failed: $errorMsg")
                    Result.failure(Exception(errorMsg))
                }
            } else {
                val errorMsg = "Login failed: ${response.message()} (${response.code()})"
                Timber.e(errorMsg)
                
                // Try to parse error body
                try {
                    val errorBody = response.errorBody()?.string()
                   Timber.d("Error body: $errorBody")
                } catch (e: Exception) {
                    Timber.e(e, "Failed to read error body")
                }
                
                Result.failure(Exception(errorMsg))
            }
        } catch (e: Exception) {
            Timber.e(e, "Login exception")
            Result.failure(e)
        }
    }

    suspend fun logout() {
        // TODO: Clear token from DataStore
        Timber.i("User logged out")
    }
}
