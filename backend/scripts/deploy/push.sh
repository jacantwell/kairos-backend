#!/bin/bash
set -e

# Load .env variables
source .env

# Create the ECR repository if it doesn't exist
if ! aws ecr describe-repositories --repository-names $STACK_NAME 2>/dev/null; then
  echo "Creating ECR repository $STACK_NAME"
  aws ecr create-repository --repository-name $STACK_NAME
fi

# Get the repository URI (without tag)
ECR_REPOSITORY="$AWS_ACCOUNT_ID.dkr.ecr.${AWS_REGION:-us-east-1}.amazonaws.com/${STACK_NAME}"

# Tag the image with the ECR repository URI and commit SHA
docker tag $STACK_NAME $ECR_REPOSITORY:$IMAGE_TAG
docker tag $STACK_NAME $ECR_REPOSITORY:latest

# Push the images to ECR
echo "Pushing image to ECR: $ECR_REPOSITORY:$IMAGE_TAG"
docker push $ECR_REPOSITORY:$IMAGE_TAG
docker push $ECR_REPOSITORY:latest

# Store the full image URI for CloudFormation
echo "ECR_REPOSITORY=$ECR_REPOSITORY" > .env
echo "IMAGE_TAG=$IMAGE_TAG" >> .env
echo "STACK_NAME=$STACK_NAME" >> .env
echo "AWS_REGION=${AWS_REGION:-us-east-1}" >> .env