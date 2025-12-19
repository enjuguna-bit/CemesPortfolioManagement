package com.arrears.manager.data.model

import com.google.gson.annotations.SerializedName

// ============================================
// API Response Wrapper
// ============================================

/**
 * Generic API response wrapper that matches the server's response structure
 * Server format: { "success": true, "data": {...}, "message": "..." }
 */
data class ApiResponse<T>(
    val success: Boolean,
    val data: T,
    val message: String? = null
)

// ============================================
// Authentication Models
// ============================================

data class LoginRequest(
    val username: String,
    val password: String
)

data class RegisterRequest(
    val username: String,
    val email: String,
    val password: String,
    @SerializedName("full_name")
    val fullName: String? = null
)

data class RefreshTokenRequest(
    @SerializedName("refresh_token")
    val refreshToken: String
)

/**
 * Authentication data structure (inside ApiResponse wrapper)
 * Matches server format: { user: {...}, access_token: "...", refresh_token: "...", contact_info: {...} }
 */
data class AuthData(
    val user: UserProfile,
    @SerializedName("access_token")
    val accessToken: String,
    @SerializedName("refresh_token")
    val refreshToken: String,
    @SerializedName("contact_info")
    val contactInfo: ContactInfo? = null
)

data class ContactInfo(
    val phone: String,
    val email: String
)

data class UserProfile(
    val id: Int,
    val username: String,
    val email: String,
    @SerializedName("full_name")
    val fullName: String?,
    val roles: List<String>,
    @SerializedName("created_at")
    val createdAt: String,
    @SerializedName("last_login")
    val lastLogin: String?,
    @SerializedName("is_active")
    val isActive: Boolean
)

data class UpdateProfileRequest(
    @SerializedName("full_name")
    val fullName: String?,
    val email: String?
)

// ============================================
// Device Models
// ============================================

data class DeviceRegistrationRequest(
    @SerializedName("device_id")
    val deviceId: String,
    @SerializedName("fcm_token")
    val fcmToken: String,
    @SerializedName("device_model")
    val deviceModel: String,
    @SerializedName("os_version")
    val osVersion: String,
    @SerializedName("app_version")
    val appVersion: String
)

data class DeviceUpdateRequest(
    @SerializedName("fcm_token")
    val fcmToken: String? = null,
    @SerializedName("app_version")
    val appVersion: String? = null
)

data class DeviceResponse(
    val id: Int,
    @SerializedName("device_id")
    val deviceId: String,
    @SerializedName("device_model")
    val deviceModel: String,
    @SerializedName("os_version")
    val osVersion: String,
    @SerializedName("app_version")
    val appVersion: String,
    @SerializedName("registered_at")
    val registeredAt: String,
    @SerializedName("last_sync")
    val lastSync: String?
)

// ============================================
// Loan Processing Models
// ============================================

data class LoanProcessingResponse(
    val data: com.google.gson.JsonElement? = null,
    val pagination: PaginationInfo? = null,
    val summary: Map<String, Any>? = null,
    val metadata: Map<String, Any>? = null,
    @SerializedName("operation_id")
    val operationId: String? = null,
    @SerializedName("download_url")
    val downloadUrl: String? = null
)

data class ArrearsCollectedResponse(
    val data: List<Map<String, Any>>? = null,
    val pagination: PaginationInfo? = null,
    val summary: ArrearsCollectedSummary,
    @SerializedName("officer_performance")
    val officerPerformance: Map<String, OfficerPerformance>? = null,
    @SerializedName("bucket_distribution")
    val bucketDistribution: Map<String, Double>? = null,
    @SerializedName("download_url")
    val downloadUrl: String? = null
)

data class ArrearsCollectedSummary(
    @SerializedName("total_collected")
    val totalCollected: Double,
    @SerializedName("total_loans_collected")
    val totalLoansCollected: Int?,
    @SerializedName("officer_count")
    val officerCount: Int,
    @SerializedName("average_collection")
    val averageCollection: Double? = null,
    @SerializedName("collection_by_officer")
    val collectionByOfficer: Map<String, Double>? = null
)

data class OfficerPerformance(
    val collected: Double,
    @SerializedName("loans_collected")
    val loansCollected: Int
)

data class MTDParametersResponse(
    val summary: MTDSummary,
    val data: List<BranchPerformance>
)

data class MTDSummary(
    @SerializedName("total_branches")
    val totalBranches: Int,
    @SerializedName("total_income")
    val totalIncome: Double,
    @SerializedName("average_cr")
    val averageCR: Double,
    @SerializedName("total_disbursement")
    val totalDisbursement: Double
)

data class BranchPerformance(
    val rank: Int,
    @SerializedName("branch_name")
    val branchName: String,
    val income: Double,
    @SerializedName("cr_percentage")
    val crPercentage: Double,
    val disbursement: Double,
    @SerializedName("performance_score")
    val performanceScore: Double
)

data class PaginationInfo(
    @SerializedName("next_cursor")
    val nextCursor: String?,
    @SerializedName("has_more")
    val hasMore: Boolean,
    val limit: Int,
    @SerializedName("total_count")
    val totalCount: Int?
)

// ============================================
// Progress Models
// ============================================

data class ProgressResponse(
    @SerializedName("operation_id")
    val operationId: String,
    @SerializedName("current_step")
    val currentStep: Int,
    @SerializedName("total_steps")
    val totalSteps: Int,
    val percentage: Double,
    val message: String,
    val metadata: Map<String, Any>? = null,
    @SerializedName("elapsed_seconds")
    val elapsedSeconds: Double,
    val completed: Boolean
)

// ============================================
// Upload Models
// ============================================

data class InitiateUploadRequest(
    val filename: String,
    @SerializedName("total_size")
    val totalSize: Long,
    @SerializedName("total_chunks")
    val totalChunks: Int
)

data class UploadSessionResponse(
    @SerializedName("session_id")
    val sessionId: String,
    val filename: String,
    @SerializedName("total_chunks")
    val totalChunks: Int,
    @SerializedName("chunk_size")
    val chunkSize: Int,
    @SerializedName("expires_at")
    val expiresAt: String
)

data class ChunkUploadResponse(
    @SerializedName("chunk_number")
    val chunkNumber: Int,
    @SerializedName("chunks_received")
    val chunksReceived: Int,
    @SerializedName("chunks_remaining")
    val chunksRemaining: Int,
    val percentage: Double
)

data class UploadCompleteResponse(
    val filename: String,
    @SerializedName("file_size")
    val fileSize: Long,
    @SerializedName("upload_time")
    val uploadTime: Double
)

data class UploadProgressResponse(
    @SerializedName("session_id")
    val sessionId: String,
    @SerializedName("chunks_uploaded")
    val chunksUploaded: Int,
    @SerializedName("total_chunks")
    val totalChunks: Int,
    val percentage: Double,
    val status: String
)

// ============================================
// Health Check
// ============================================

data class HealthResponse(
    val status: String,
    val timestamp: String,
    val version: String,
    val database: String,
    val services: Map<String, String>
)

// ============================================
// Error Response
// ============================================

data class ErrorResponse(
    val error: String,
    val message: String,
    val code: String? = null,
    @SerializedName("correlation_id")
    val correlationId: String? = null,
    val details: Map<String, Any>? = null
)
