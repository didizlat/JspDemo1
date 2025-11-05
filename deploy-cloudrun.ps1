Param(
  [string]$ProjectId,
  [string]$Region = "us-central1",
  [string]$Service = "jspdemo1",
  [string]$JdbcUrl,
  [string]$DbUser,
  [string]$DbPass
)

if (-not $ProjectId -or -not $JdbcUrl -or -not $DbUser -or -not $DbPass) {
  Write-Host "Usage: .\deploy-cloudrun.ps1 -ProjectId <id> -JdbcUrl <jdbc> -DbUser <user> -DbPass <pass> [-Region us-central1]" -ForegroundColor Yellow
  exit 1
}

$image = "gcr.io/$ProjectId/jspdemo1"

gcloud auth login
gcloud config set project $ProjectId
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

gcloud builds submit --tag $image

gcloud run deploy $Service `
  --image $image `
  --region $Region `
  --allow-unauthenticated `
  --set-env-vars "SPRING_PROFILES_ACTIVE=cloud,SPRING_DATASOURCE_URL=$JdbcUrl,SPRING_DATASOURCE_USERNAME=$DbUser,SPRING_DATASOURCE_PASSWORD=$DbPass"


