# GCP Authentication Setup Guide

## Problem
Error: `Your default credentials were not found. To set up Application Default Credentials...`

## Solutions (Choose One)

### ✅ Option 1: Use gcloud CLI (Recommended for Local Development)

This is the easiest method for local development:

```bash
# 1. Install gcloud CLI (if not installed)
# Download from: https://cloud.google.com/sdk/docs/install

# 2. Authenticate with your Google account
gcloud auth application-default login

# 3. Set your project
gcloud config set project YOUR_PROJECT_ID

# 4. Verify authentication
gcloud auth list

# 5. Restart your application
source venv/bin/activate
python app_new.py
```

**Pros:**
- ✅ Easy to set up
- ✅ No need to manage key files
- ✅ Uses your personal Google account
- ✅ Good for development

**Cons:**
- ❌ Not suitable for production
- ❌ Requires gcloud CLI installed

---

### ✅ Option 2: Use Service Account Key File (Production)

Best for production deployments and CI/CD:

```bash
# 1. Create a service account in GCP Console
# Go to: https://console.cloud.google.com/iam-admin/serviceaccounts
# - Select your project
# - Click "Create Service Account"
# - Give it a name (e.g., "blinky-api-service")
# - Grant roles: "Vertex AI User", "Discovery Engine Admin"

# 2. Create and download key
# - Click on the service account
# - Go to "Keys" tab
# - Click "Add Key" → "Create new key" → JSON
# - Save the file (e.g., gcp-credentials.json)

# 3. Set environment variable
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/gcp-credentials.json"

# Or add to your .env file:
echo 'GOOGLE_APPLICATION_CREDENTIALS=/path/to/gcp-credentials.json' >> .env

# 4. Restart your application
source venv/bin/activate
python app_new.py
```

**Pros:**
- ✅ Works in production
- ✅ Works in Docker containers
- ✅ Works in CI/CD pipelines
- ✅ Fine-grained permissions

**Cons:**
- ❌ Need to manage key files securely
- ❌ Keys should never be committed to git

---

### ✅ Option 3: Run Without GCP (Temporary Fix)

I've already updated the code to handle missing credentials gracefully. The app will now:
- ✅ Start successfully without GCP credentials
- ✅ Show a warning message
- ✅ Return a friendly error message to users when AI is needed

**Current behavior:**
```
Error initializing Vertex AI: Your default credentials were not found...
Application will continue without AI capabilities
```

When users try to chat, they'll receive:
```
"Lo siento, el servicio de IA no está disponible en este momento. Por favor, contacta al administrador."
```

---

## For Docker Deployment

### Method 1: Mount credentials file
```bash
docker run -p 5003:5003 \
  -v /path/to/gcp-credentials.json:/app/gcp-credentials.json:ro \
  -e GOOGLE_APPLICATION_CREDENTIALS=/app/gcp-credentials.json \
  --env-file .env \
  blinky-base-api:optimized
```

### Method 2: Use gcloud in container
```dockerfile
# Add to Dockerfile
RUN apt-get update && apt-get install -y curl
RUN curl https://sdk.cloud.google.com | bash
```

---

## Security Best Practices

### ⚠️ NEVER commit credentials to git

Add to `.gitignore`:
```
# GCP Credentials
gcp-credentials.json
*-credentials.json
*.json
!package.json
```

### ✅ Use Secret Management in Production

For production, use:
- **GCP Secret Manager**: Store credentials securely
- **Kubernetes Secrets**: For K8s deployments
- **Cloud Run**: Uses Workload Identity (no keys needed!)
- **GKE**: Uses Workload Identity Federation

---

## Verify Setup

Test your authentication:

```bash
# Test with Python
python -c "from google.cloud import aiplatform; print('✓ Auth working!')"

# Test with gcloud
gcloud auth application-default print-access-token
```

---

## Troubleshooting

### Issue: "Permission denied"
**Solution:** Ensure your service account has the required roles:
- Vertex AI User
- Discovery Engine Admin (if using RAG)

### Issue: "Project not found"
**Solution:** Verify `GCP_PROJECT_ID` in your `.env` file matches your actual GCP project ID

### Issue: "Quota exceeded"
**Solution:** Check your GCP quotas and billing

---

## Environment Variables Required

Make sure these are set in your `.env` file:

```bash
# Required
GCP_PROJECT_ID=your-project-id
GCP_LOCATION=us-central1

# Optional (for RAG)
RAG_CORPUS_NAME=your-corpus-name

# For authentication (choose one method)
GOOGLE_APPLICATION_CREDENTIALS=/path/to/credentials.json
```
