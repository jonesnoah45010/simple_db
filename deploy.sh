#!/bin/bash

SERVICE_NAME="noahs-user-management" # Define your service name here. Example "test-portal"

# Step 1: Build and push the container image
gcloud builds submit --tag gcr.io/teachmemedical/${SERVICE_NAME} .

# Step 2: Deploy the Cloud Run service 
gcloud run deploy ${SERVICE_NAME} \
    --image=gcr.io/teachmemedical/${SERVICE_NAME} \
    --vpc-connector dev-connector \
    --region=us-east1 \
    --allow-unauthenticated \
    --platform managed \
    --project teachmemedical  \
    --quiet