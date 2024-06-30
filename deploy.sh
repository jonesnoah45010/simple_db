#!/bin/bash

SERVICE_NAME="YOUR_SERVICE_NAME" # Define your service name here. Example "test-service"
PROJECT_NAME="YOUR_GCLOUD_PROJECT" # Define your gcloud project id here
VPC_CONNECTOR="YOUR_VPC_CONNECTOR" # Define your gcloud mysql vpc-connector

# Step 1: Build and push the container image
gcloud builds submit --tag gcr.io/${PROJECT_NAME}/${SERVICE_NAME} .

# Step 2: Deploy the Cloud Run service 
gcloud run deploy ${SERVICE_NAME} \
    --image=gcr.io/${PROJECT_NAME}/${SERVICE_NAME} \
    --vpc-connector ${VPC_CONNECTOR} \
    --region=us-east1 \
    --allow-unauthenticated \
    --platform managed \
    --project ${PROJECT_NAME}  \
    --quiet
