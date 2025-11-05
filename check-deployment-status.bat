@echo off
echo ========================================
echo   Cloud Run Deployment Status Check
echo ========================================
echo.

set GCLOUD="C:\Program Files (x86)\Google\Cloud SDK\google-cloud-sdk\bin\gcloud.cmd"

echo Checking recent builds...
echo.
%GCLOUD% builds list --limit=3 --format="table(id,status,createTime)" --project=jspdemo1
echo.

echo Checking Cloud Run services...
echo.
%GCLOUD% run services list --region us-east1 --project=jspdemo1
echo.

echo If service exists, getting URL...
echo.
%GCLOUD% run services describe jspdemo1 --region us-east1 --format="value(status.url)" --project=jspdemo1 2>nul
if errorlevel 1 (
    echo Service not found yet - deployment may still be in progress.
) else (
    echo.
    echo Service URL retrieved above!
)
echo.
pause

