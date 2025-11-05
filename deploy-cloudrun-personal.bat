@echo off
title Cloud Run Deployment - JSP Demo
color 0A
echo ========================================
echo   Cloud Run Deployment Script
echo   JSP Demo Application
echo ========================================
echo.
echo NOTE: This script requires your personal Google account
echo       (not the service account) for API enablement and building.
echo.

set GCLOUD="C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"

echo [Step 1/5] Checking authentication...
%GCLOUD% auth list
echo.
echo If you see your personal account above, press any key to continue.
echo If not, the script will prompt you to login.
pause
echo.

echo [Step 2/5] Enabling required APIs...
echo Note: This requires your personal Google account with Owner/Editor role.
%GCLOUD% services enable cloudresourcemanager.googleapis.com run.googleapis.com cloudbuild.googleapis.com containerregistry.googleapis.com artifactregistry.googleapis.com --project=jspdemo1
if errorlevel 1 (
    echo.
    echo WARNING: API enablement failed. You may need to enable them manually:
    echo https://console.cloud.google.com/apis/library?project=jspdemo1
    echo.
    echo Press any key to continue anyway (if APIs are already enabled)...
    pause
)
echo OK
echo.

echo [Step 3/5] Setting project to jspdemo1...
%GCLOUD% config set project jspdemo1
echo OK
echo.

echo [Step 4/5] Building container image...
echo This will take 5-10 minutes. Please wait...
echo.
cd /d C:\Users\dylan\CursorProjects\JspDemo1
%GCLOUD% builds submit --tag gcr.io/jspdemo1/jspdemo1 --project=jspdemo1
if errorlevel 1 (
    echo.
    echo ERROR: Container build failed!
    echo Make sure you're authenticated with: gcloud auth login
    pause
    exit /b 1
)
echo OK
echo.

echo [Step 5/5] Deploying to Cloud Run...
echo This will take 2-3 minutes. Please wait...
echo.
%GCLOUD% run deploy jspdemo1 --image gcr.io/jspdemo1/jspdemo1 --region us-east1 --allow-unauthenticated --set-env-vars "SPRING_PROFILES_ACTIVE=cloud,SPRING_DATASOURCE_URL=jdbc:postgresql://ep-fancy-dew-a4pl2mmr-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require,SPRING_DATASOURCE_USERNAME=neondb_owner,SPRING_DATASOURCE_PASSWORD=npg_7HBEAFnPxKt1" --project=jspdemo1
if errorlevel 1 (
    echo.
    echo ERROR: Deployment failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   DEPLOYMENT SUCCESSFUL!
echo ========================================
echo.
echo Your application is now deployed!
echo The Cloud Run URL will be displayed above.
echo Copy that URL to access your application.
echo.
echo To get the URL again, run:
echo   gcloud run services describe jspdemo1 --region us-east1 --format="value(status.url)"
echo.
pause

