# Deploy to Google Cloud Run (free tier)

This project is ready to deploy to Cloud Run using a container image.

## Prerequisites
- Google account + project (free tier ok)
- gcloud CLI installed and logged in
- A Postgres instance (Neon free is recommended)

## 1) Create a free Postgres (Neon)
- Create database and copy connection details
- Build JDBC URL: `jdbc:postgresql://HOST/DB?sslmode=require`

## 2) Build and push container
```bash
PROJECT_ID=YOUR_GCP_PROJECT_ID
REGION=us-central1
IMAGE=gcr.io/$PROJECT_ID/jspdemo1

# From repo root
gcloud auth login
gcloud config set project $PROJECT_ID
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

gcloud builds submit --tag $IMAGE
```

## 3) Deploy to Cloud Run
```bash
gcloud run deploy jspdemo1 \
  --image $IMAGE \
  --region $REGION \
  --allow-unauthenticated \
  --set-env-vars "SPRING_PROFILES_ACTIVE=cloud,SPRING_DATASOURCE_URL=jdbc:postgresql://HOST/DB?sslmode=require,SPRING_DATASOURCE_USERNAME=USER,SPRING_DATASOURCE_PASSWORD=PASS"
```

Output includes a public HTTPS URL.

## Notes
- `SPRING_PROFILES_ACTIVE=cloud` switches to Postgres and binds `server.port` to `$PORT`.
- H2 remains for local development.
- You can redeploy with updated image any time using the same command.

