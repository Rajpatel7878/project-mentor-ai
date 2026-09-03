# PowerShell deploy script for Google Cloud Run

param(
    [string]$ProjectId = "your-project-id",
    [string]$Region = "us-central1"
)

$ErrorActionPreference = "Stop"

Write-Host "Deploying Project Mentor AI to Cloud Run..." -ForegroundColor Cyan

# Deploy backend
Write-Host "Deploying backend..." -ForegroundColor Yellow
gcloud run deploy mentor-ai-backend `
    --source ./backend `
    --region $Region `
    --project $ProjectId `
    --allow-unauthenticated `
    --set-env-vars "GEMINI_API_KEY=$env:GEMINI_API_KEY,FIRESTORE_PROJECT_ID=$ProjectId,ALLOW_SYSTEM_CONTROL=false" `
    --memory 2Gi `
    --cpu 2 `
    --timeout 300

$BackendUrl = gcloud run services describe mentor-ai-backend --region $Region --project $ProjectId --format "value(status.url)"
Write-Host "Backend URL: $BackendUrl" -ForegroundColor Green

# Deploy frontend
$WsUrl = $BackendUrl -replace "https://", "wss://"
Write-Host "Deploying frontend..." -ForegroundColor Yellow
gcloud run deploy mentor-ai-frontend `
    --source ./frontend `
    --region $Region `
    --project $ProjectId `
    --allow-unauthenticated `
    --set-env-vars "NEXT_PUBLIC_API_URL=$BackendUrl,NEXT_PUBLIC_WS_URL=$WsUrl" `
    --memory 512Mi

$FrontendUrl = gcloud run services describe mentor-ai-frontend --region $Region --project $ProjectId --format "value(status.url)"
Write-Host ""
Write-Host "Deployment complete!" -ForegroundColor Green
Write-Host "Frontend: $FrontendUrl"
Write-Host "Backend:  $BackendUrl"
