package com.arrears.manager.presentation.auth

import androidx.lifecycle.ViewModel
import androidx.lifecycle.viewModelScope
import com.arrears.manager.data.repository.AuthRepository
import dagger.hilt.android.lifecycle.HiltViewModel
import kotlinx.coroutines.flow.*
import kotlinx.coroutines.launch
import timber.log.Timber
import javax.inject.Inject

data class LoginUiState(
    val isLoading: Boolean = false,
    val isLoggedIn: Boolean = false,
    val error: String? = null
)

@HiltViewModel
class LoginViewModel @Inject constructor(
    private val authRepository: AuthRepository
) : ViewModel() {

    private val _uiState = MutableStateFlow(LoginUiState())
    val uiState: StateFlow<LoginUiState> = _uiState.asStateFlow()
    
    val isLoggedIn: Flow<Boolean> = authRepository.isLoggedIn

    fun login(username: String, password: String) {
        viewModelScope.launch {
            _uiState.update { it.copy(isLoading = true, error = null) }
            
            authRepository.login(username, password)
                .onSuccess { response ->
                    Timber.d("Login successful: ${response.user.username}")
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            isLoggedIn = true,
                            error = null
                        )
                    }
                }
                .onFailure { error ->
                    Timber.e(error, "Login failed")
                    _uiState.update {
                        it.copy(
                            isLoading = false,
                            isLoggedIn = false,
                            error = error.message ?: "Login failed. Please try again."
                        )
                    }
                }
        }
    }
    
    fun logout() {
        viewModelScope.launch {
            authRepository.logout()
            _uiState.update { LoginUiState() }
        }
    }
}
