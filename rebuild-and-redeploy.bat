@echo off
echo ========================================
echo   Rebuilding and Redeploying
echo   with JSP Packaging Fix
echo ========================================
echo.

echo Step 1: Rebuilding container (5-10 minutes)...
gcloud builds submit --tag gcr.io/jspdemo1/jspdemo1 --project=jspdemo1
if errorlevel 1 (
    echo ERROR: Build failed!
    pause
    exit /b 1
)

echo.
echo Step 2: Redeploying to Cloud Run (2-3 minutes)...
gcloud run deploy jspdemo1 --image gcr.io/jspdemo1/jspdemo1 --region us-east1 --allow-unauthenticated --set-env-vars "SPRING_PROFILES_ACTIVE=cloud,SPRING_DATASOURCE_URL=jdbc:postgresql://ep-fancy-dew-a4pl2mmr-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require,SPRING_DATASOURCE_USERNAME=neondb_owner,SPRING_DATASOURCE_PASSWORD=npg_7HBEAFnPxKt1" --project=jspdemo1
if errorlevel 1 (
    echo ERROR: Deployment failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Deployment Complete!
echo ========================================
echo.
echo Your app URL will be shown above.
echo.
pause


