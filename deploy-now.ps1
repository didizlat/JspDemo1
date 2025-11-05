# Cloud Run Deployment Script
$gcloud = "C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"

Write-Host "Step 1: Authenticating with service account..." -ForegroundColor Cyan
& $gcloud auth activate-service-account --key-file "C:\Users\dylan\Downloads\jspdemo1-84a23c888c9d.json"

Write-Host "`nStep 2: Setting project..." -ForegroundColor Cyan
& $gcloud config set project jspdemo1

Write-Host "`nStep 3: Enabling required APIs..." -ForegroundColor Cyan
& $gcloud services enable run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com artifactregistry.googleapis.com

Write-Host "`nStep 4: Building container image (this may take 5-10 minutes)..." -ForegroundColor Cyan
cd C:\Users\dylan\CursorProjects\JspDemo1
& $gcloud builds submit --tag gcr.io/jspdemo1/jspdemo1

Write-Host "`nStep 5: Deploying to Cloud Run (this may take 2-3 minutes)..." -ForegroundColor Cyan
& $gcloud run deploy jspdemo1 `
  --image gcr.io/jspdemo1/jspdemo1 `
  --region us-east1 `
  --allow-unauthenticated `
  --set-env-vars "SPRING_PROFILES_ACTIVE=cloud,SPRING_DATASOURCE_URL=jdbc:postgresql://ep-fancy-dew-a4pl2mmr-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require,SPRING_DATASOURCE_USERNAME=neondb_owner,SPRING_DATASOURCE_PASSWORD=npg_7HBEAFnPxKt1"

Write-Host "`n✅ Deployment complete! Your app URL will be shown above." -ForegroundColor Green


