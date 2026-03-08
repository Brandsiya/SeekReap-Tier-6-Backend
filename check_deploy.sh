#!/bin/bash
REGION="us-central1"
BACKEND_URL="https://seekreap-backend-tif2gmgi4q-uc.a.run.app"

echo "🔍 Checking SeekReap Services in $REGION..."
echo "----------------------------------------"

# Check Cloud Run Service Status
gcloud run services list --region=$REGION --format="table(metadata.name,status.conditions[0].status,status.address.url)"

echo ""
echo "🌐 Testing Backend Health Endpoint..."
curl -s -o /dev/null -w "HTTP Status: %{http_code}\n" "$BACKEND_URL/health"

echo ""
echo "📜 Fetching latest Worker logs (last 5 lines)..."
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=seekreap-worker" --limit=5 --format="value(textPayload)"
