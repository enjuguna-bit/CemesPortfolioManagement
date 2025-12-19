package com.arrears.manager.data.api

import com.arrears.manager.data.model.*
import okhttp3.MultipartBody
import okhttp3.RequestBody
import retrofit2.Response
import retrofit2.http.*

/**
 * Retrofit API interface for Arrears Manager backend
 */
interface ArrearsApiService {

    // ============================================
    // Authentication Endpoints
    // ============================================

    @POST("auth/login")
    suspend fun login(@Body request: LoginRequest): Response<ApiResponse<AuthData>>

    @POST("auth/register")
    suspend fun register(@Body request: RegisterRequest): Response<ApiResponse<AuthData>>

    @POST("auth/refresh")
    suspend fun refreshToken(@Body request: RefreshTokenRequest): Response<ApiResponse<AuthData>>

    @POST("auth/logout")
    suspend fun logout(): Response<ApiResponse<Unit>>

    @GET("auth/me")
    suspend fun getProfile(): Response<ApiResponse<UserProfile>>

    @PUT("auth/profile")
    suspend fun updateProfile(@Body request: UpdateProfileRequest): Response<ApiResponse<UserProfile>>

    // ============================================
    // Device Management
    // ============================================

    @POST("devices/register")
    suspend fun registerDevice(@Body request: DeviceRegistrationRequest): Response<ApiResponse<DeviceResponse>>

    @PUT("devices/{deviceId}")
    suspend fun updateDevice(
        @Path("deviceId") deviceId: String,
        @Body request: DeviceUpdateRequest
    ): Response<ApiResponse<DeviceResponse>>

    @DELETE("devices/{deviceId}")
    suspend fun unregisterDevice(@Path("deviceId") deviceId: String): Response<ApiResponse<Unit>>

    @GET("devices")
    suspend fun getDevices(): Response<ApiResponse<List<DeviceResponse>>>

    // ============================================
    // Loan Processing Endpoints
    // ============================================

    @Multipart
    @POST("loans/dormant-arrangement")
    suspend fun processDormantArrangement(
        @Part file: MultipartBody.Part,
        @Query("branch_name") branchName: String? = null,
        @Query("limit") limit: Int? = null,
        @Query("cursor") cursor: String? = null
    ): Response<ApiResponse<LoanProcessingResponse>>

    @Multipart
    @POST("loans/arrears-collected")
    suspend fun processArrearsCollected(
        @Part sodFile: MultipartBody.Part,
        @Part curFile: MultipartBody.Part,
        @Part("officer_targets") officerTargets: RequestBody? = null
    ): Response<ApiResponse<ArrearsCollectedResponse>>

    @Multipart
    @POST("loans/arrange-dues")
    suspend fun processArrangeDues(
        @Part file: MultipartBody.Part
    ): Response<ApiResponse<LoanProcessingResponse>>

    @Multipart
    @POST("loans/arrange-arrears")
    suspend fun processArrangeArrears(
        @Part file: MultipartBody.Part
    ): Response<ApiResponse<LoanProcessingResponse>>

    @Multipart
    @POST("loans/mtd-parameters")
    suspend fun processMTDParameters(
        @Part incomeFile: MultipartBody.Part,
        @Part crFile: MultipartBody.Part,
        @Part disbFile: MultipartBody.Part
    ): Response<ApiResponse<MTDParametersResponse>>

    @Multipart
    @POST("loans/mtd-unpaid-dues")
    suspend fun processMTDUnpaidDues(
        @Part file: MultipartBody.Part
    ): Response<ApiResponse<LoanProcessingResponse>>

    // ============================================
    // Progress Tracking
    // ============================================

    @GET("loans/progress/{operationId}")
    suspend fun getProcessingProgress(
        @Path("operationId") operationId: String
    ): Response<ProgressResponse>

    // ============================================
    // Chunked File Upload
    // ============================================

    @POST("uploads/initiate")
    suspend fun initiateUpload(@Body request: InitiateUploadRequest): Response<UploadSessionResponse>

    @Multipart
    @POST("uploads/{sessionId}/chunk")
    suspend fun uploadChunk(
        @Path("sessionId") sessionId: String,
        @Part("chunk_number") chunkNumber: RequestBody,
        @Part file: MultipartBody.Part
    ): Response<ChunkUploadResponse>

    @POST("uploads/{sessionId}/complete")
    suspend fun completeUpload(
        @Path("sessionId") sessionId: String
    ): Response<UploadCompleteResponse>

    @DELETE("uploads/{sessionId}")
    suspend fun cancelUpload(
        @Path("sessionId") sessionId: String
    ): Response<Unit>

    @GET("uploads/{sessionId}/progress")
    suspend fun getUploadProgress(
        @Path("sessionId") sessionId: String
    ): Response<UploadProgressResponse>

    // ============================================
    // Health Check
    // ============================================

    @GET("../health")
    suspend fun healthCheck(): Response<HealthResponse>
}
