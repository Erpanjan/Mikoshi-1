# Quick Start Guide

## 1. Setup Environment

### Create .env file
```bash
cp env.example .env
# Edit .env and fill in your values
```

### Required Environment Variables
- `API_SECRET`: Secret key for API key generation (use a strong random string)
- `GCS_BUCKET_NAME`: Your Google Cloud Storage bucket name
- `GCS_PROJECT_ID`: Your Google Cloud Project ID
- `GCS_CREDENTIALS_PATH`: (Optional) Path to service account JSON file
- `PORT`: (Optional) Server port, default: 8080

## 2. Setup Python Virtual Environment (Recommended for Local Development)

### Create Virtual Environment

```bash
cd api
python3 -m venv .venv
```

### Activate Virtual Environment

**On macOS/Linux:**
```bash
source .venv/bin/activate
```

**On Windows:**
```bash
.venv\Scripts\activate
```

### Install Dependencies

```bash
pip install -r requirements.txt
```

**Note:** If you prefer to use system Python instead of a virtual environment, you can skip this step and install dependencies directly with `pip install -r requirements.txt`.

## 3. Generate API Key

**Note:** Before generating, make sure you have API_SECRET variable set in .env file. 
```bash
cd api
python generate_api_key.py
```

Copy the generated API key - you'll need it for API requests.

## 4. Run Locally

### Option A: Direct Python (Recommended)

**Make sure your virtual environment is activated:**
```bash
# Navigate to api directory
cd api

# Activate virtual environment
source .venv/bin/activate  # macOS/Linux
# OR: .venv\Scripts\activate  # Windows

# Make sure you have file called gac.json and variable GCS_CREDENTIALS_PATH inside of .env file to point to this gac.json. 
# To download this file, go to Google Cloud Console -> Service Accounts -> neo-engine-api -> Keys -> create new key for yourself

# Run the application (reads HOST and PORT from .env)
python app.py
```

The application will read `HOST` and `PORT` from your `.env` file (defaults to `0.0.0.0:8080`).

### Option B: Using Docker
```bash
# Build image, make sure you are not in `api` folder itself
docker build -f api/Dockerfile -t neo-engine-api .

# Run container with environment variables
# IMPORTANT: --env-file works with docker run, NOT docker build
docker run -p 8080:8080 --env-file api/.env neo-engine-api

# Or pass environment variables directly
docker run -p 8080:8080 \
  -e API_SECRET=your-secret \
  -e GCS_BUCKET_NAME=your-bucket \
  -e GCS_PROJECT_ID=your-project \
  -e GCS_CREDENTIALS_PATH=/path/to/credentials.json \
  neo-engine-api
```

### Option C: Using Docker Compose
```bash
docker-compose -f api/docker-compose.yml up
```

## 5. Test the API

```bash
# Set your API key
export API_KEY=$(python api/generate_api_key.py | grep "X-Api-Key:" | cut -d' ' -f2)

# Run test script
bash api/test_api.sh
```

Or manually test:

```bash
# Health check
curl http://localhost:8080/health

# Generate portfolio (synchronous)
curl -X POST http://localhost:8080/neo/api/v1/generate \
  -H "X-Api-Key: $API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "storageId": "test_user",
    "fileName": "portfolio_v1",
    "riskProfile": "RP1",
    "weightType": "dynamic"
  }'
```

## 6. Deploy to Google Cloud Run

```bash
# Build and deploy
gcloud run deploy neo-engine-api \
  --source . \
  --platform managed \
  --region asia-east2 \
  --set-env-vars API_SECRET=your-secret,GCS_BUCKET_NAME=your-bucket,GCS_PROJECT_ID=your-project \
  --allow-unauthenticated \
  --memory 2Gi \
  --timeout 300
```

**Note:** Make sure your Cloud Run service account has:
- Storage Object Admin role on the GCS bucket
- Permission to generate signed URLs

## Troubleshooting

### GCS Authentication Issues
- Ensure service account has proper IAM roles
- Check that credentials file path is correct
- For Cloud Run, ensure service account has Storage permissions

### Import Errors
- Make sure you're running from the project root
- Check that PYTHONPATH includes the SAA Model directory

### Port Already in Use
- Change PORT in .env file
- Or use a different port: `PORT=8081 python -m api.app`

