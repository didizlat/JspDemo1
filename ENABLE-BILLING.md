# Enable Billing for Cloud Run Deployment

## Issue
Cloud Run, Cloud Build, Container Registry, and Artifact Registry require billing to be enabled, even though they have free tiers.

## Solution: Enable Billing

### Step 1: Enable Billing
1. Go to: https://console.cloud.google.com/billing?project=jspdemo1
2. Click "Link a billing account" or "Create billing account"
3. If you don't have a billing account:
   - Click "Create Account"
   - Enter your payment information (Google Cloud provides $300 free credit for new accounts)
   - Complete the setup

### Step 2: Verify Billing is Enabled
After enabling billing, wait 1-2 minutes for it to propagate, then run:

```cmd
gcloud billing projects describe jspdemo1
```

You should see your billing account listed.

### Step 3: Enable APIs
Once billing is enabled, run:

```cmd
gcloud services enable cloudresourcemanager.googleapis.com run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com artifactregistry.googleapis.com --project=jspdemo1
```

### Step 4: Continue Deployment
After APIs are enabled, run:

```cmd
.\deploy-cloudrun-personal.bat
```

## Note on Free Tier
- Cloud Run: 2 million requests/month free
- Cloud Build: 120 build-minutes/day free
- Container Registry: 0.5 GB storage free
- You likely won't be charged for this demo project

