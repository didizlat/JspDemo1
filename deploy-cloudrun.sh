#!/bin/bash
# Cloud Run Deployment Script for Git Bash

GCLOUD="C:/Program Files (x86)/Google/Cloud SDK/google-cloud-sdk/bin/gcloud.cmd"

echo "========================================"
echo "  Cloud Run Deployment - JSP Demo"
echo "========================================"
echo ""

echo "[Step 1/5] Authenticating with service account..."
"$GCLOUD" auth activate-service-account --key-file "C:/Users/dylan/Downloads/jspdemo1-84a23c888c9d.json"
if [ $? -ne 0 ]; then
    echo "ERROR: Authentication failed!"
    exit 1
fi
echo "✓ OK"
echo ""

echo "[Step 2/5] Setting project to jspdemo1..."
"$GCLOUD" config set project jspdemo1
echo "✓ OK"
echo ""

echo "[Step 3/5] Enabling required APIs..."
"$GCLOUD" services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com artifactregistry.googleapis.com
echo "✓ OK"
echo ""

echo "[Step 4/5] Building container image..."
echo "This will take 5-10 minutes. Please wait..."
echo ""
cd /c/Users/dylan/CursorProjects/JspDemo1
"$GCLOUD" builds submit --tag gcr.io/jspdemo1/jspdemo1
if [ $? -ne 0 ]; then
    echo "ERROR: Container build failed!"
    exit 1
fi
echo "✓ OK"
echo ""

echo "[Step 5/5] Deploying to Cloud Run..."
echo "This will take 2-3 minutes. Please wait..."
echo ""
"$GCLOUD" run deploy jspdemo1 \
  --image gcr.io/jspdemo1/jspdemo1 \
  --region us-east1 \
  --allow-unauthenticated \
  --set-env-vars "SPRING_PROFILES_ACTIVE=cloud,SPRING_DATASOURCE_URL=jdbc:postgresql://ep-fancy-dew-a4pl2mmr-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require,SPRING_DATASOURCE_USERNAME=neondb_owner,SPRING_DATASOURCE_PASSWORD=npg_7HBEAFnPxKt1"
if [ $? -ne 0 ]; then
    echo "ERROR: Deployment failed!"
    exit 1
fi

echo ""
echo "========================================"
echo "  DEPLOYMENT SUCCESSFUL!"
echo "========================================"
echo ""
echo "Your application is now deployed!"
echo "The Cloud Run URL will be displayed above."
echo "Copy that URL to access your application."
echo ""
echo "To get the URL again, run:"
echo '  gcloud run services describe jspdemo1 --region us-east1 --format="value(status.url)"'
echo ""
