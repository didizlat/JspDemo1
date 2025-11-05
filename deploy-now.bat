@echo off
echo Deploying to Cloud Run...
echo This will take 2-3 minutes...
echo.
gcloud run deploy jspdemo1 --image gcr.io/jspdemo1/jspdemo1 --region us-east1 --allow-unauthenticated --set-env-vars "SPRING_PROFILES_ACTIVE=cloud,SPRING_DATASOURCE_URL=jdbc:postgresql://ep-fancy-dew-a4pl2mmr-pooler.us-east-1.aws.neon.tech/neondb?sslmode=require,SPRING_DATASOURCE_USERNAME=neondb_owner,SPRING_DATASOURCE_PASSWORD=npg_7HBEAFnPxKt1" --project=jspdemo1
echo.
echo Deployment complete! Your URL will be shown above.
pause
