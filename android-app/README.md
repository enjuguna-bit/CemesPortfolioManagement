# Arrears Manager Android App

Modern Android application for loan arrears management with real-time processing and beautiful UI.

## Features

- 🔐 **Secure Authentication** - JWT-based login with device binding
- 📊 **Loan Processing** - Process 6 different types of loan reports
- 📤 **Smart File Upload** - Chunked uploads with resume capability
- 📈 **Real-time Progress** - Live progress tracking with beautiful animations
- 🎨 **Premium UI** - Material Design 3 with dynamic theming
- 🌙 **Dark Mode** - Full dark mode support
- 📱 **Offline Support** - Local caching and sync
- 🔔 **Push Notifications** - Firebase Cloud Messaging integration

## Tech Stack

- **Language**: Kotlin
- **UI**: Jetpack Compose + Material Design 3
- **Architecture**: MVVM + Clean Architecture
- **Networking**: Retrofit + OkHttp
- **Async**: Kotlin Coroutines + Flow
- **DI**: Hilt (Dagger)
- **Local DB**: Room
- **Image Loading**: Coil
- **Push Notifications**: Firebase Cloud Messaging

## Project Structure

```
app/
├── src/main/
│   ├── java/com/arrears/manager/
│   │   ├── data/
│   │   │   ├── api/          # API interfaces
│   │   │   ├── model/        # Data models
│   │   │   ├── repository/   # Data repositories
│   │   │   └── local/        # Room database
│   │   ├── domain/
│   │   │   ├── usecase/      # Business logic
│   │   │   └── model/        # Domain models
│   │   ├── presentation/
│   │   │   ├── auth/         # Login/Register screens
│   │   │   ├── home/         # Dashboard
│   │   │   ├── loans/        # Loan processing
│   │   │   ├── upload/       # File upload
│   │   │   └── settings/     # Settings
│   │   ├── ui/
│   │   │   ├── components/   # Reusable components
│   │   │   └── theme/        # App theme
│   │   └── util/             # Utilities
│   └── res/
│       ├── drawable/         # Icons and images
│       ├── values/           # Strings, colors, themes
│       └── xml/              # XML resources
```

## Setup

1. **Clone the repository**
2. **Open in Android Studio**
3. **Configure API endpoint** in `local.properties`:
   ```properties
   api.base.url=https://your-server.com/api/v1/
   ```
4. **Add Firebase configuration** - Download `google-services.json`
5. **Build and run**

## API Integration

The app integrates with the Flask API server:
- Base URL: `/api/v1/`
- Authentication: JWT Bearer tokens
- File uploads: Chunked multipart/form-data
- Progress tracking: Polling endpoint

## Screenshots

[Screenshots will be added here]

## License

Proprietary - All rights reserved
