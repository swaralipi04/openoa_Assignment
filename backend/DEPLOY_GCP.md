# Deploying OpenOA Backend to GCP Cloud Run

## Prerequisites

1. **Docker Desktop** installed and running
2. **Docker Hub account** — [hub.docker.com](https://hub.docker.com) (free)
3. **GCP account** with a project — [console.cloud.google.com](https://console.cloud.google.com)
4. **gcloud CLI** installed — [cloud.google.com/sdk/docs/install](https://cloud.google.com/sdk/docs/install)

---

## Step 1: Build the Docker Image

```bash
cd /Users/swara/Desktop/openoa-app/backend

# Build for linux/amd64 (Cloud Run requires amd64, your Mac is arm64)
docker build --platform linux/amd64 -t openoa-backend .
```

> **Note:** The `--platform linux/amd64` flag is critical on Apple Silicon Macs.
> The build will take 5-10 minutes (installs scipy, numpy, openoa, etc.).

---

## Step 2: Test Locally (Optional but Recommended)

```bash
docker run -p 8000:8000 openoa-backend
```

Open [http://localhost:8000/api/health](http://localhost:8000/api/health) — should return `{"status": "healthy"}`.

---

## Step 3: Push to Docker Hub

```bash
# Login to Docker Hub
docker login

# Tag the image (replace YOUR_DOCKERHUB_USERNAME)
docker tag openoa-backend YOUR_DOCKERHUB_USERNAME/openoa-backend:latest

# Push
docker push YOUR_DOCKERHUB_USERNAME/openoa-backend:latest
```

---

## Step 4: Deploy to Cloud Run

### Option A: Using gcloud CLI (Recommended)

```bash
# Login to GCP
gcloud auth login

# Set your project
gcloud config set project YOUR_PROJECT_ID

# Deploy from Docker Hub image
gcloud run deploy openoa-backend \
    --image docker.io/YOUR_DOCKERHUB_USERNAME/openoa-backend:latest \
    --platform managed \
    --region asia-south1 \
    --port 8000 \
    --memory 2Gi \
    --cpu 2 \
    --timeout 300 \
    --concurrency 10 \
    --min-instances 0 \
    --max-instances 3 \
    --allow-unauthenticated
```

**Key flags explained:**
| Flag | Value | Why |
|------|-------|-----|
| `--memory 2Gi` | 2 GB RAM | OpenOA analyses load large DataFrames into memory |
| `--cpu 2` | 2 vCPUs | Monte Carlo simulations are CPU-intensive |
| `--timeout 300` | 5 minutes | Analyses can take 30-120 seconds |
| `--concurrency 10` | 10 requests/instance | Low because each analysis uses ~1 GB RAM |
| `--allow-unauthenticated` | Public access | So your frontend can call it without auth |
| `--region asia-south1` | Mumbai | Closest to India. Change if needed |

### Option B: Using GCP Console (UI)

1. Go to [console.cloud.google.com/run](https://console.cloud.google.com/run)
2. Click **"Create Service"**
3. Select **"Deploy one revision from an existing container image"**
4. Enter: `docker.io/YOUR_DOCKERHUB_USERNAME/openoa-backend:latest`
5. Set:
   - Service name: `openoa-backend`
   - Region: `asia-south1` (Mumbai)
   - CPU allocation: **CPU is always allocated**
   - Memory: **2 GiB**
   - CPU: **2**
   - Request timeout: **300 seconds**
   - Maximum concurrent requests: **10**
   - Min instances: **0**, Max instances: **3**
6. Under **Authentication**: Select **"Allow unauthenticated invocations"**
7. Click **"Create"**

---

## Step 5: Get Your Cloud Run URL

After deployment, Cloud Run gives you a URL like:
```
https://openoa-backend-xxxx-el.a.run.app
```

Test it:
```bash
curl https://openoa-backend-xxxx-el.a.run.app/api/health
# Should return: {"status":"healthy","openoa_version":"3.x"}
```

---

## Step 6: Connect Frontend to Cloud Run Backend

Update your frontend's `api.js` to point to the Cloud Run URL:

```javascript
// src/api.js
const API_BASE = 'https://openoa-backend-xxxx-el.a.run.app';
```

Or better, use environment variables:
```javascript
const API_BASE = import.meta.env.VITE_API_BASE || '';
```

Then when deploying frontend:
```bash
VITE_API_BASE=https://openoa-backend-xxxx-el.a.run.app npm run build
```

---

## About the .data_cache Files

The CSV data files (~105 MB) are **baked into the Docker image** via:
```dockerfile
COPY .data_cache/*.csv ./.data_cache/
```

This means:
- ✅ No external dependencies — the image is self-contained
- ✅ Example data loads instantly (no download needed)
- ⚠️ Image is larger (~1.5 GB with all Python deps + data)

### Alternative: Google Cloud Storage (if image size is a concern)

If you want a smaller image, you could store the CSVs in a GCS bucket instead:

1. Upload to GCS:
```bash
gsutil mb gs://openoa-data
gsutil cp .data_cache/*.csv gs://openoa-data/la-haute-borne/
```

2. Modify `data_service.py` to download from GCS instead of local `.data_cache/`
3. Remove the `COPY .data_cache/` line from Dockerfile

For a demo/portfolio project, baking into the image is simpler and recommended.

---

## Cost Estimate (GCP Free Tier)

Cloud Run offers a generous free tier:
- **2 million requests/month** — free
- **360,000 GB-seconds** of memory — free
- **180,000 vCPU-seconds** — free

With `min-instances: 0`, you pay **nothing when idle**. Each analysis call (~60s × 2GB) uses ~120 GB-seconds, so you can run ~3,000 free analyses/month.

---

## Troubleshooting

| Issue | Fix |
|-------|-----|
| Build fails on Mac with scipy | Add `--platform linux/amd64` to docker build |
| Cloud Run returns 503 | Increase `--memory` to 4Gi |
| Analysis times out | Increase `--timeout` to 600 |
| CORS errors from frontend | Backend already has `allow_origins=["*"]` — should work. If not, check the Cloud Run URL in frontend api.js |
| Image push fails | Make sure `docker login` succeeded and repo name matches |
