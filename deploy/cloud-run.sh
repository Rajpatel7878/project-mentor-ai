#!/bin/bash
# Deploy Project Mentor AI to Google Cloud Run

set -e

PROJECT_ID=${GCP_PROJECT_ID:-"your-project-id"}
REGION=${GCP_REGION:-"us-central1"}
GEMINI_API_KEY=${GEMINI_API_KEY:-""}

echo "Deploying Project Mentor AI to Cloud Run..."
echo "Project: $PROJECT_ID | Region: $REGION"

# Build and deploy backend
echo "Deploying backend..."
gcloud run deploy mentor-ai-backend \
  --source ./backend \
  --region $REGION \
  --project $PROJECT_ID \
  --allow-unauthenticated \
  --set-env-vars "GEMINI_API_KEY=$GEMINI_API_KEY,FIRESTORE_PROJECT_ID=$PROJECT_ID,ALLOW_SYSTEM_CONTROL=false" \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --min-instances 0 \
  --max-instances 3

BACKEND_URL=$(gcloud run services describe mentor-ai-backend --region $REGION --project $PROJECT_ID --format 'value(status.url)')
echo "Backend URL: $BACKEND_URL"

# Build and deploy frontend
echo "Deploying frontend..."
gcloud run deploy mentor-ai-frontend \
  --source ./frontend \
  --region $REGION \
  --project $PROJECT_ID \
  --allow-unauthenticated \
  --set-env-vars "NEXT_PUBLIC_API_URL=$BACKEND_URL,NEXT_PUBLIC_WS_URL=${BACKEND_URL/https/wss}" \
  --memory 512Mi \
  --min-instances 0 \
  --max-instances 2

FRONTEND_URL=$(gcloud run services describe mentor-ai-frontend --region $REGION --project $PROJECT_ID --format 'value(status.url)')
echo ""
echo "Deployment complete!"
echo "Frontend: $FRONTEND_URL"
echo "Backend:  $BACKEND_URL"
