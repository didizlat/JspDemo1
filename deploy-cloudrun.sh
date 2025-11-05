#!/usr/bin/env bash
set -euo pipefail

PROJECT_ID=${PROJECT_ID:?set PROJECT_ID}
REGION=${REGION:-us-central1}
SERVICE=${SERVICE:-jspdemo1}
JDBC_URL=${SPRING_DATASOURCE_URL:?set SPRING_DATASOURCE_URL}
DB_USER=${SPRING_DATASOURCE_USERNAME:?set SPRING_DATASOURCE_USERNAME}
DB_PASS=${SPRING_DATASOURCE_PASSWORD:?set SPRING_DATASOURCE_PASSWORD}

IMAGE=gcr.io/$PROJECT_ID/jspdemo1

gcloud auth login
gcloud config set project "$PROJECT_ID"
gcloud services enable run.googleapis.com cloudbuild.googleapis.com

gcloud builds submit --tag "$IMAGE"

gcloud run deploy "$SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" \
  --allow-unauthenticated \
  --set-env-vars "SPRING_PROFILES_ACTIVE=cloud,SPRING_DATASOURCE_URL=$JDBC_URL,SPRING_DATASOURCE_USERNAME=$DB_USER,SPRING_DATASOURCE_PASSWORD=$DB_PASS"


