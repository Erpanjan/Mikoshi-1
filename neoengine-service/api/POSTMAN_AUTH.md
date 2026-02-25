# Postman Authentication for Cloud Run

If your Cloud Run service requires authentication (not using `--allow-unauthenticated`), you need to pass a Google Cloud identity token in your requests.

## Option 1: Using gcloud CLI (Easiest for Testing)

### Step 1: Get Identity Token

**Note:** Easiest way for this is eather to install gcloud locally and login, or go to google cloud console on web, launch actual console and run the command to get token

```bash
# Get an identity token for your Cloud Run service
gcloud auth print-identity-token --audiences=https://YOUR-SERVICE-URL
```

Example:
```bash
gcloud auth print-identity-token --audiences=https://neo-engine-api-dev-321746168225.asia-east2.run.app
```

This will output a JWT token that's valid for 1 hour.

### Step 2: Use in Postman

1. In Postman, go to the **Authorization** tab
2. Select **Bearer Token** as the type
3. Paste the token from Step 1
4. Make your request

**Note:** The token expires after 1 hour, so you'll need to regenerate it.

## Option 2: Using Service Account (For Production/CI)

### Step 1: Create a Service Account (if you don't have one)

```bash
gcloud iam service-accounts create postman-client \
    --display-name="Postman Client Service Account"
```

### Step 2: Grant Cloud Run Invoker Role

```bash
gcloud run services add-iam-policy-binding neo-engine-api-dev \
    --region asia-east2 \
    --member="serviceAccount:postman-client@YOUR_PROJECT_ID.iam.gserviceaccount.com" \
    --role="roles/run.invoker"
```

### Step 3: Create and Download Key

```bash
gcloud iam service-accounts keys create postman-key.json \
    --iam-account=postman-client@YOUR_PROJECT_ID.iam.gserviceaccount.com
```

### Step 4: Get Identity Token Using Service Account

```bash
# Authenticate with the service account
gcloud auth activate-service-account --key-file=postman-key.json

# Get identity token
gcloud auth print-identity-token --audiences=https://YOUR-SERVICE-URL
```

## Option 3: Postman Pre-request Script (Automated)

You can automate token generation in Postman using a pre-request script:

1. In Postman, go to your request
2. Click on the **Pre-request Script** tab
3. Add this script (requires `gcloud` CLI to be installed and authenticated):

```javascript
// Note: This requires gcloud CLI to be installed
// This is a simplified example - you may need to adjust based on your setup
const { exec } = require('child_process');
const serviceUrl = pm.environment.get("CLOUD_RUN_URL");

exec(`gcloud auth print-identity-token --audiences=${serviceUrl}`, (error, stdout, stderr) => {
    if (error) {
        console.error(`Error: ${error.message}`);
        return;
    }
    const token = stdout.trim();
    pm.environment.set("GCP_IDENTITY_TOKEN", token);
    pm.request.headers.add({
        key: 'Authorization',
        value: `Bearer ${token}`
    });
});
```

## Option 4: Use Postman's OAuth 2.0 (Advanced)

Postman supports OAuth 2.0 with Google Cloud. You can configure it to automatically get tokens.

1. In Postman, go to **Authorization** tab
2. Select **OAuth 2.0**
3. Configure:
   - **Grant Type**: Client Credentials
   - **Access Token URL**: `https://oauth2.googleapis.com/token`
   - **Client ID**: Your service account client ID
   - **Client Secret**: Your service account private key
   - **Scope**: `https://www.googleapis.com/auth/cloud-platform`

## Recommendation

For quick testing: Use **Option 1** (gcloud CLI)
For production/automated testing: Use **Option 2** (Service Account)

## Important Notes

- Identity tokens expire after 1 hour
- The token must match the service URL (audience)
- You still need to pass your API key in the `X-Api-Key` header for your Flask app authentication
- Cloud Run authentication (Bearer token) is separate from your app's API key authentication

## Complete Postman Setup

1. **Authorization Header**: `Bearer <gcloud-identity-token>` (for Cloud Run)
2. **X-Api-Key Header**: `<your-api-key>` (for Flask app)
3. **Content-Type**: `application/json`

Example headers:
```
Authorization: Bearer eyJhbGciOiJSUzI1NiIsImtpZCI6...
X-Api-Key: your-generated-api-key-here
Content-Type: application/json
```

