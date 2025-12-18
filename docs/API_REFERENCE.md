# API Endpoint Reference

## Base URL
```
Development: http://localhost:5000
Production: https://your-domain.com
```

## Authentication

All endpoints except `/health` and `/api/v1/auth/*` require JWT authentication.

**Header Format:**
```
Authorization: Bearer <access_token>
```

---

## Endpoints

### Health Check

```http
GET /health
GET /api/health
```

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2025-12-18T08:12:41Z",
  "api_version": "v1",
  "services": {
    "api": "operational",
    "database": "connected"
  }
}
```

---

### Authentication

#### Register User
```http
POST /api/v1/auth/register
Content-Type: application/json

{
  "username": "string",
  "email": "string",
  "password": "string",
  "full_name": "string" (optional)
}
```

#### Login
```http
POST /api/v1/auth/login
Content-Type: application/json

{
  "username": "string",
  "password": "string"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "user": {...},
    "access_token": "eyJ...",
    "refresh_token": "eyJ..."
  }
}
```

#### Refresh Token
```http
POST /api/v1/auth/refresh
Content-Type: application/json

{
  "refresh_token": "string"
}
```

---

### Device Management

#### Register Device
```http
POST /api/v1/devices/register
Authorization: Bearer <token>
Content-Type: application/json

{
  "device_id": "string",
  "platform": "android",
  "fcm_token": "string",
  "device_model": "string",
  "os_version": "string",
  "app_version": "string"
}
```

#### List Devices
```http
GET /api/v1/devices/
Authorization: Bearer <token>
```

---

### File Uploads (Chunked)

#### Initiate Upload
```http
POST /api/v1/uploads/initiate
Authorization: Bearer <token>
Content-Type: application/json

{
  "filename": "data.csv",
  "file_size": 52428800,
  "total_chunks": 50
}
```

#### Upload Chunk
```http
POST /api/v1/uploads/chunk
Authorization: Bearer <token>
X-Upload-Id: <session_id>
X-Chunk-Number: 1
Content-Type: multipart/form-data

chunk: <binary data>
```

#### Complete Upload
```http
POST /api/v1/uploads/complete
Authorization: Bearer <token>
Content-Type: application/json

{
  "session_id": "string"
}
```

---

### Loan Processing

#### Arrange Dues
```http
POST /api/v1/loans/arrange-dues?limit=20&fields=FieldOfficer,TotalArrears
Authorization: Bearer <token>
Content-Type: multipart/form-data

file: <csv file>
```

**Query Parameters:**
- `limit`: Page size (default: 20, max: 100)
- `after`: Pagination cursor
- `fields`: Comma-separated field names for partial response

**Response:**
```json
{
  "success": true,
  "data": [...],
  "pagination": {
    "next_cursor": "eyJ...",
    "has_more": true,
    "limit": 20,
    "total_count": 150
  },
  "summary": {
    "total_clients": 500,
    "officer_count": 25,
    "total_amount_due": 1500000.00,
    "total_arrears": 250000.00
  }
}
```

#### Other Loan Endpoints

- `POST /api/v1/loans/dormant-arrangement` - Process dormant arrangements
- `POST /api/v1/loans/arrears-collected` - Arrears collection analysis
- `POST /api/v1/loans/arrange-arrears` - Arrears bucketing
- `POST /api/v1/loans/mtd-unpaid-dues` - Risk analysis

All support pagination and field selection.

---

## Error Responses

**Format:**
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Missing required fields: username, password",
    "timestamp": "2025-12-18T08:12:41Z",
    "correlation_id": "uuid-here"
  }
}
```

**Error Codes:**
- `VALIDATION_ERROR` (400) - Invalid input
- `AUTHENTICATION_ERROR` (401) - Invalid or missing token
- `AUTHORIZATION_ERROR` (403) - Insufficient permissions
- `NOT_FOUND` (404) - Resource not found
- `RATE_LIMIT_EXCEEDED` (429) - Too many requests
- `SERVER_ERROR` (500) - Internal server error

---

## Rate Limiting

**Default Limits:**
- 100 requests per hour per IP
- 200 requests per hour per authenticated user

**Headers:**
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1702900000
```

**429 Response:**
```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Rate limit exceeded"
  }
}
```
**Header:** `Retry-After: 3600`
