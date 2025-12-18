# Quick Start Guide

## Installation

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Set up environment
cp .env.example .env
# Edit .env with your configuration

# 3. Initialize database
python -c "from app import app, db; app.app_context().push(); db.create_all()"

# 4. Run development server
python app.py
```

## First API Call

```bash
# Register a user
curl -X POST http://localhost:5000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "secure_password_123"
  }'

# Response includes access_token - use it for authenticated requests
```

## Android Integration Example (Kotlin)

```kotlin
// 1. Register device
val deviceRequest = DeviceRegistrationRequest(
    deviceId = Settings.Secure.getString(contentResolver, Settings.Secure.ANDROID_ID),
    platform = "android",
    fcmToken = FirebaseMessaging.getInstance().token.await(),
    deviceModel = Build.MODEL,
    osVersion = Build.VERSION.RELEASE,
    appVersion = BuildConfig.VERSION_NAME
)

val response = apiService.registerDevice(deviceRequest)

// 2. Upload file with chunked transfer
val uploadSession = apiService.initiateUpload(
    filename = file.name,
    fileSize = file.length(),
    totalChunks = (file.length() / CHUNK_SIZE).toInt() + 1
)

// Upload chunks
file.inputStream().use { input ->
    var chunkNumber = 1
    val buffer = ByteArray(CHUNK_SIZE)
    var bytesRead: Int
    
    while (input.read(buffer).also { bytesRead = it } != -1) {
        val chunk = buffer.copyOf(bytesRead)
        apiService.uploadChunk(
            sessionId = uploadSession.sessionId,
            chunkNumber = chunkNumber++,
            chunk = chunk
        )
    }
}

// Complete upload
apiService.completeUpload(uploadSession.sessionId)
```

## Production Deployment

```bash
# Using Gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 --worker-class gevent app:app

# Using Docker
docker build -t arrears-manager-api .
docker run -p 5000:5000 --env-file .env arrears-manager-api
```
