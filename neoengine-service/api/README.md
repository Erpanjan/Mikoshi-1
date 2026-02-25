# Neo-Engine API Server

Flask web server for running portfolio optimization pipelines via REST API.

## Features

- **REST API**: `/neo/api/v1/generate` endpoint for portfolio optimization
- **API Key Authentication**: Protected by X-Api-Key header
- **Google Cloud Storage**: Automatic upload of results with presigned URLs
- **Webhook Support**: Optional async processing with webhook callbacks
- **Docker Support**: Containerized for easy deployment

## Setup

### 1. Environment Variables

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

Required variables:
- `API_SECRET`: Secret key for API key generation
- `GCS_BUCKET_NAME`: Google Cloud Storage bucket name
- `GCS_PROJECT_ID`: Google Cloud Project ID
- `GCS_CREDENTIALS_PATH`: (Optional) Path to service account JSON file
- `PORT`: (Optional) Server port (default: 8080)

### 2. Generate API Key

```bash
python generate_api_key.py
```

This will generate an API key that you can use in the `X-Api-Key` header.

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Run Locally

```bash
python -m api.app
```

Or using Flask directly:

```bash
export FLASK_APP=api.app
flask run --host=0.0.0.0 --port=8080
```

## API Usage

### Generate Portfolio Optimization

**Endpoint:** `POST /neo/api/v1/generate`

**Headers:**
```
X-Api-Key: <your-api-key>
Content-Type: application/json
```

**Request Body:**
```json
{
  "storageId": "user123",
  "fileName": "portfolio_v1",
  "riskProfile": "RP1",
  "weightType": "dynamic",
  "webhook": {
    "url": "https://example.com/webhook",
    "method": "POST",
    "headers": {
      "Authorization": "Bearer token123"
    }
  }
}
```

**Required Fields:**
- `storageId`: Namespace for storing results in GCS
- `fileName`: File name/version identifier

**Optional Fields:**
- `riskProfile`: Risk profile (default: "RP1")
- `weightType`: "dynamic" or "equilibrium" (default: "dynamic")
- `webhook`: Webhook configuration for async processing

**Response (Synchronous - no webhook):**
```json
{
  "status": "completed",
  "files": {
    "saaResults": "https://storage.googleapis.com/...",
    "portfolioResults": "https://storage.googleapis.com/..."
  }
}
```

**Response (Asynchronous - with webhook):**
```json
{
  "status": "processing",
  "message": "Request accepted and processing started"
}
```

The webhook will be called with:
```json
{
  "storageId": "user123",
  "fileName": "portfolio_v1",
  "status": "completed",
  "files": {
    "saaResults": "https://...",
    "portfolioResults": "https://..."
  }
}
```

### Optimize Portfolio (JSON Response)

**Endpoint:** `POST /neo/api/v1/optimize`

Returns layered optimization output as JSON (no GCS upload).

**Request Body:**
```json
{
  "risk_profile": "RP3",
  "target_volatility": 0.10,
  "active_risk_percentage": 0.30,
  "weight_type": "dynamic",
  "investment_amount": 1000000
}
```

Notes:
- `active_risk_percentage` is optional.
- If provided, it overrides Layer 2 active risk split.
- Accepts decimal (`0.30`) or percent (`30`) input.

### Health Check

**Endpoint:** `GET /health`

Returns server health status.

## Docker

### Build Image

```bash
docker build -t neo-engine-api .
```

### Run Container

```bash
docker run -p 8080:8080 \
  -e API_SECRET=your-secret \
  -e GCS_BUCKET_NAME=your-bucket \
  -e GCS_PROJECT_ID=your-project \
  neo-engine-api
```

Or with .env file:

```bash
docker run -p 8080:8080 --env-file .env neo-engine-api
```

### Deploy to Google Cloud Run

```bash
gcloud run deploy neo-engine-api \
  --source . \
  --platform managed \
  --region us-central1 \
  --set-env-vars API_SECRET=your-secret,GCS_BUCKET_NAME=your-bucket,GCS_PROJECT_ID=your-project \
  --allow-unauthenticated
```

## Error Responses

### 401 Unauthorized
```json
{
  "error": "Unauthorized",
  "message": "Invalid or missing API key"
}
```

### 422 Validation Error
```json
{
  "storageId": [
    {"message": "storageId is required", "code": "REQUIRED"}
  ],
  "fileName": [
    {"message": "fileName is required", "code": "REQUIRED"}
  ]
}
```

### 400 Bad Request (Invalid Webhook)
```json
{
  "error": "webhook method must be POST",
  "code": "INVALID_METHOD"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "message": "Error details..."
}
```

## Notes

- Presigned URLs are valid for 1 hour
- Files are stored in GCS at: `{storageId}/{fileName}/SAA_Results.xlsx` and `{storageId}/{fileName}/Portfolio_Construction_Results.xlsx`
- When webhook is provided, processing happens asynchronously and the API returns immediately
- Without webhook, the API waits for processing to complete before returning
