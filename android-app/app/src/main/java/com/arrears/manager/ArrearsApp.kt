package com.arrears.manager

import android.app.Application
import android.app.NotificationChannel
import android.app.NotificationManager
import android.os.Build
import androidx.work.Configuration
import dagger.hilt.android.HiltAndroidApp
import timber.log.Timber

@HiltAndroidApp
class ArrearsApp : Application(), Configuration.Provider {

    override fun onCreate() {
        super.onCreate()
        
        // Initialize Timber for logging
        if (BuildConfig.DEBUG) {
            Timber.plant(Timber.DebugTree())
        }
        
        // Create notification channels
        createNotificationChannels()
        
        Timber.d("ArrearsApp initialized")
    }

    override val workManagerConfiguration: Configuration
        get() = Configuration.Builder()
            .setMinimumLoggingLevel(if (BuildConfig.DEBUG) android.util.Log.DEBUG else android.util.Log.ERROR)
            .build()

    private fun createNotificationChannels() {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channels = listOf(
                NotificationChannel(
                    CHANNEL_PROCESSING,
                    "Processing Notifications",
                    NotificationManager.IMPORTANCE_LOW
                ).apply {
                    description = "Notifications for loan processing status"
                },
                NotificationChannel(
                    CHANNEL_ALERTS,
                    "Alerts",
                    NotificationManager.IMPORTANCE_HIGH
                ).apply {
                    description = "Important alerts and notifications"
                },
                NotificationChannel(
                    CHANNEL_UPLOADS,
                    "File Uploads",
                    NotificationManager.IMPORTANCE_LOW
                ).apply {
                    description = "File upload progress notifications"
                }
            )

            val notificationManager = getSystemService(NotificationManager::class.java)
            channels.forEach { notificationManager.createNotificationChannel(it) }
        }
    }

    companion object {
        const val CHANNEL_PROCESSING = "processing"
        const val CHANNEL_ALERTS = "alerts"
        const val CHANNEL_UPLOADS = "uploads"
    }
}
