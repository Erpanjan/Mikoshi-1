# Google Cloud Run Deployment Guide

This guide explains how to set up and deploy the Neo-Engine API to Google Cloud Run using GitHub Actions.

## Prerequisites

1. **Google Cloud Project** with billing enabled
2. **Service Accounts** created in GCP:
   - Deployment service account which can both auth with google cloud and deploy to cloud run

### Required permissions for service account for cloud run e.g GCP_DEPLOY_SERVICE_ACCOUNT (gcdeploy.json)

- roles/run.admin
- roles/artifactregistry.writer
- roles/iam.serviceAccountUser
-

### Required permissions for service account on google storage e.g  GCS_CREDENTIALS_PATH (gcs.json)

- roles/storage.objectAdmin


