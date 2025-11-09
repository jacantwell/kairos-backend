# Deployment Guide

## Overview

Kairos backend is deployed on AWS Lambda using a containerized approach with Docker and AWS CloudFormation for infrastructure as code. The deployment pipeline is automated via GitHub Actions.

## Architecture

```
┌──────────────┐    ┌─────────────┐    ┌──────────────┐
│   GitHub     │───▶│   GitHub    │───▶│     ECR      │
│   (main)     │    │   Actions   │    │  (Container) │
└──────────────┘    └─────────────┘    └──────────────┘
                            │                    │
                            ▼                    ▼
                    ┌─────────────┐    ┌──────────────┐
                    │ CloudForm-  │───▶│    Lambda    │
                    │   ation     │    │  Function    │
                    └─────────────┘    └──────────────┘
                                              │
                                              ▼
                                       ┌──────────────┐
                                       │ API Gateway  │
                                       └──────────────┘
```

## Prerequisites

### AWS Account Setup

1. **AWS Account:** Active AWS account with appropriate permissions
2. **IAM User:** Create IAM user with programmatic access
3. **Required Permissions:**
   - ECR (Elastic Container Registry)
   - Lambda
   - API Gateway
   - CloudFormation
   - IAM (for role creation)
   - CloudWatch Logs

### Required Tools

- **Docker:** Version 20.10 or higher
- **AWS CLI:** Version 2.x
- **Poetry:** Python dependency management
- **Git:** Version control

### Installation

```bash
# Install AWS CLI (macOS)
brew install awscli

# Install AWS CLI (Linux)
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
sudo ./aws/install

# Install Docker (varies by OS)
# See: https://docs.docker.com/get-docker/

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -
```

## Configuration

### Environment Variables

Create a `.env` file in the project root:

```env
# Stack Configuration
STACK_NAME=kairos-backend
AWS_REGION=eu-west-2
AWS_ACCOUNT_ID=992382417038
REPO_NAME=kairos

# MongoDB Atlas
MONGO_HOST=cluster0.mongodb.net
MONGO_USERNAME=your_username
MONGO_PASSWORD=your_password
MONGO_DB_NAME=kairos

# Email Service (Resend)
MAIL_USERNAME=resend
MAIL_FROM=send.findkairos.com
MAIL_PORT=587
MAIL_SERVER=smtp.resend.com
RESEND_API_KEY=re_xxxxxxxxxxxx

# Security
SECRET_KEY=your_long_random_secret_key_here
```

### AWS CLI Configuration

```bash
# Configure AWS credentials
aws configure

# Output:
# AWS Access Key ID: YOUR_ACCESS_KEY
# AWS Secret Access Key: YOUR_SECRET_KEY
# Default region name: eu-west-2
# Default output format: json

# Verify configuration
aws sts get-caller-identity
```

## Manual Deployment

### Step 1: Build Docker Image

Build the Lambda-compatible Docker image:

```bash
sh scripts/deploy/build.sh
```

This script:
- Loads environment variables from `.env`
- Builds Docker image with tag `$STACK_NAME`
- Uses `Dockerfile` with Python 3.12 Lambda base image

**Dockerfile Overview:**

```dockerfile
FROM public.ecr.aws/lambda/python:3.12

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 -
ENV PATH="/root/.local/bin:$PATH"

# Copy dependencies
COPY pyproject.toml poetry.lock ./

# Install dependencies (no virtualenv)
RUN poetry config virtualenvs.create false && \
    poetry install --no-interaction --no-ansi --no-root

# Copy application code
COPY kairos/ ./kairos/

# Set Lambda handler
CMD [ "kairos.main.handler" ]
```

### Step 2: Push to ECR

Push the Docker image to AWS Elastic Container Registry:

```bash
# Login to ECR
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com

# Run push script
sh scripts/deploy/push.sh
```

This script:
1. Creates ECR repository if it doesn't exist
2. Tags image with `latest` and commit SHA
3. Pushes both tags to ECR
4. Exports image URI for CloudFormation

**Manual ECR Commands:**

```bash
# Create repository
aws ecr create-repository --repository-name kairos

# Tag image
docker tag kairos-backend \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/kairos:latest

# Push image
docker push \
  $AWS_ACCOUNT_ID.dkr.ecr.$AWS_REGION.amazonaws.com/kairos:latest

# Get image digest
aws ecr describe-images \
  --repository-name kairos \
  --image-ids imageTag=latest \
  --query 'imageDetails[0].imageDigest' \
  --output text
```

### Step 3: Deploy with CloudFormation

Deploy the infrastructure and Lambda function:

```bash
aws cloudformation deploy \
  --capabilities CAPABILITY_IAM \
  --stack-name kairos-backend \
  --template-file template.yaml \
  --region eu-west-2 \
  --parameter-overrides \
    ImageUri="$ECR_REPOSITORY@$IMAGE_DIGEST" \
    MongoUsername="$MONGO_USERNAME" \
    MongoPassword="$MONGO_PASSWORD" \
    MongoHost="$MONGO_HOST" \
    MongoDbName="$MONGO_DB_NAME" \
    MailUsername="$MAIL_USERNAME" \
    ResendApiKey="$RESEND_API_KEY" \
    SecretKey="$SECRET_KEY"
```

**CloudFormation Template Components:**

- **LambdaExecutionRole:** IAM role with CloudWatch Logs permissions
- **LambdaFunction:** Container-based Lambda (15s timeout, 256MB memory)
- **ApiGateway:** HTTP API Gateway v2
- **ApiIntegration:** Lambda proxy integration
- **ApiRoute:** Catch-all route `ANY /{proxy+}`
- **ApiDeployment & ApiStage:** Deployment to default stage
- **LambdaPermission:** API Gateway invoke permission

### Step 4: Get API Endpoint

Retrieve the deployed API Gateway URL:

```bash
aws cloudformation describe-stacks \
  --stack-name kairos-backend \
  --query "Stacks[0].Outputs[?ExportName=='kairos-backend-ApiEndpoint'].OutputValue" \
  --output text
```

Output example:
```
https://7zpmbpgf7d.execute-api.eu-west-2.amazonaws.com
```

### Step 5: Test Deployment

```bash
# Test health endpoint
curl https://your-api-id.execute-api.eu-west-2.amazonaws.com/api/v1/

# Test MongoDB connection
curl https://your-api-id.execute-api.eu-west-2.amazonaws.com/api/v1/mongodb

# View API documentation
open https://your-api-id.execute-api.eu-west-2.amazonaws.com/docs
```

## Automated Deployment (CI/CD)

### GitHub Actions Setup

The repository includes a GitHub Actions workflow (`.github/workflows/deploy_backend.yml`) that automatically deploys on push to `main`.

### Required GitHub Secrets

Configure these secrets in your GitHub repository:

**Settings → Secrets and variables → Actions → New repository secret**

1. **AWS_ACCESS_KEY_ID** - AWS IAM user access key
2. **AWS_SECRET_ACCESS_KEY** - AWS IAM user secret key
3. **MONGO_USERNAME** - MongoDB Atlas username
4. **MONGO_PASSWORD** - MongoDB Atlas password
5. **MONGO_HOST** - MongoDB Atlas host (e.g., cluster0.mongodb.net)
6. **MONGO_DB_NAME** - MongoDB database name
7. **MAIL_USERNAME** - Email service username (usually "resend")
8. **RESEND_API_KEY** - Resend API key for sending emails
9. **SECRET_KEY** - JWT secret key (generate with `openssl rand -hex 32`)
10. **KAIROS_API_CLIENT_TS_PAT** - Personal access token for triggering client repo updates

### Workflow Overview

```yaml
name: Build, Push, and Deploy

on:
  push:
    branches: [ main ]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - Checkout code
      - Configure AWS credentials
      - Login to ECR
      - Create ECR repository (if needed)
      - Build Docker image
      - Push to ECR
      - Deploy via CloudFormation
      - Output API Gateway URL
  
  dispatch:
    needs: deploy-backend
    steps:
      - Get version from pyproject.toml
      - Trigger client repository update
```

### Triggering a Deployment

```bash
# Make changes
git add .
git commit -m "feat: add new feature"
git push origin main

# GitHub Actions will automatically:
# 1. Build Docker image
# 2. Push to ECR
# 3. Deploy to Lambda
# 4. Output API URL
# 5. Trigger client repo update
```

### Monitoring Deployment

View deployment progress:

1. Go to GitHub repository
2. Click "Actions" tab
3. Click on the running workflow
4. Monitor each step in real-time

View CloudFormation events:

```bash
aws cloudformation describe-stack-events \
  --stack-name kairos-backend \
  --max-items 20
```

## Stack Updates

### Updating Lambda Code

To update just the Lambda function code (without infrastructure changes):

```bash
# Build new image
sh scripts/deploy/build.sh

# Push to ECR
sh scripts/deploy/push.sh

# Update Lambda function
aws lambda update-function-code \
  --function-name kairos-backend \
  --image-uri $ECR_REPOSITORY:latest
```

### Updating Infrastructure

To update CloudFormation stack:

```bash
# Modify template.yaml
# Then deploy
aws cloudformation deploy \
  --capabilities CAPABILITY_IAM \
  --stack-name kairos-backend \
  --template-file template.yaml \
  # ... other parameters
```

### Rolling Back

CloudFormation maintains stack history:

```bash
# List stack events
aws cloudformation describe-stack-events \
  --stack-name kairos-backend

# Rollback to previous version
aws cloudformation rollback-stack \
  --stack-name kairos-backend
```

## Environment-Specific Deployments

### Development Environment

```bash
# Use separate stack
STACK_NAME=kairos-backend-dev
MONGO_DB_NAME=kairos_dev

aws cloudformation deploy \
  --stack-name kairos-backend-dev \
  # ... deploy with dev settings
```

### Staging Environment

```bash
STACK_NAME=kairos-backend-staging
MONGO_DB_NAME=kairos_staging

aws cloudformation deploy \
  --stack-name kairos-backend-staging \
  # ... deploy with staging settings
```

### Production Environment

```bash
STACK_NAME=kairos-backend-prod
MONGO_DB_NAME=kairos_prod

aws cloudformation deploy \
  --stack-name kairos-backend-prod \
  # ... deploy with production settings
```

## Configuration Management

### Lambda Configuration

Current settings in `template.yaml`:

```yaml
LambdaFunction:
  Type: AWS::Lambda::Function
  Properties:
    Timeout: 15              # Seconds (API Gateway max: 30s)
    MemorySize: 256          # MB (128-10240 MB)
    PackageType: Image
```

**Tuning Recommendations:**

- **Memory:** Monitor CloudWatch metrics, increase if needed
- **Timeout:** Keep under API Gateway limit (30s)
- **Environment Variables:** Use Systems Manager Parameter Store for sensitive data

### API Gateway Configuration

Current settings:

```yaml
ApiGateway:
  Type: AWS::ApiGatewayV2::Api
  Properties:
    Name: !Ref AWS::StackName
    ProtocolType: HTTP       # HTTP API (cheaper than REST)
```

**Custom Domain (Future Enhancement):**

```yaml
ApiDomainName:
  Type: AWS::ApiGatewayV2::DomainName
  Properties:
    DomainName: api.findkairos.com
    DomainNameConfigurations:
      - CertificateArn: !Ref Certificate
```

## Monitoring and Logging

### CloudWatch Logs

Lambda logs are automatically sent to CloudWatch:

```bash
# View logs
aws logs tail /aws/lambda/kairos-backend --follow

# Query logs
aws logs filter-log-events \
  --log-group-name /aws/lambda/kairos-backend \
  --filter-pattern "ERROR"

# Get log insights
aws logs start-query \
  --log-group-name /aws/lambda/kairos-backend \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --query-string 'fields @timestamp, @message | filter @message like /ERROR/'
```

### CloudWatch Metrics

Key metrics to monitor:

- **Invocations:** Number of Lambda invocations
- **Duration:** Execution time
- **Errors:** Failed invocations
- **Throttles:** Rate-limited requests
- **ConcurrentExecutions:** Concurrent Lambda executions

```bash
# Get Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Duration \
  --dimensions Name=FunctionName,Value=kairos-backend \
  --start-time $(date -u -d '1 hour ago' +%s) \
  --end-time $(date -u +%s) \
  --period 300 \
  --statistics Average,Maximum
```

### Setting Up Alarms

```yaml
# In template.yaml
LambdaErrorAlarm:
  Type: AWS::CloudWatch::Alarm
  Properties:
    AlarmName: kairos-backend-errors
    MetricName: Errors
    Namespace: AWS/Lambda
    Statistic: Sum
    Period: 300
    EvaluationPeriods: 1
    Threshold: 5
    ComparisonOperator: GreaterThanThreshold
    AlarmActions:
      - !Ref SNSTopicArn
```

## Performance Optimization

### Cold Start Optimization

**Current cold start:** ~2-3 seconds with Poetry dependencies

**Optimization strategies:**

1. **Reduce Dependencies:**
   ```bash
   # Review installed packages
   poetry show --tree
   
   # Remove unused dependencies
   poetry remove package_name
   ```

2. **Use Lambda Layers:**
   ```yaml
   LambdaLayer:
     Type: AWS::Lambda::LayerVersion
     Properties:
       Content:
         S3Bucket: my-bucket
         S3Key: dependencies-layer.zip
       CompatibleRuntimes:
         - python3.12
   ```

3. **Provisioned Concurrency:**
   ```yaml
   ProvisionedConcurrency:
     Type: AWS::Lambda::Alias
     Properties:
       FunctionName: !Ref LambdaFunction
       ProvisionedConcurrencyConfig:
         ProvisionedConcurrentExecutions: 2
   ```

### Memory Optimization

Monitor and adjust Lambda memory:

```bash
# Get Lambda configuration
aws lambda get-function-configuration \
  --function-name kairos-backend

# Update memory
aws lambda update-function-configuration \
  --function-name kairos-backend \
  --memory-size 512
```

**Cost vs Performance:**
- More memory = faster CPU = potentially lower cost
- Test with different memory sizes
- Monitor CloudWatch metrics

### Database Connection Pooling

FastAPI uses MongoDB's async driver with connection pooling.

**Optimize in `kairos/database/main.py`:**

```python
client = AsyncMongoClient(
    mongo_uri,
    maxPoolSize=10,          # Limit concurrent connections
    minPoolSize=1,           # Minimum connections
    maxIdleTimeMS=30000,     # Close idle connections
)
```

## Security Best Practices

### Environment Variables

**Never commit secrets:**

```bash
# Ensure .env is in .gitignore
echo ".env" >> .gitignore
```

**Use AWS Systems Manager Parameter Store:**

```bash
# Store secret
aws ssm put-parameter \
  --name /kairos/prod/mongo-password \
  --value "secret_password" \
  --type SecureString

# In template.yaml, reference:
Environment:
  Variables:
    MONGO_PASSWORD: !Sub '{{resolve:ssm:/kairos/prod/mongo-password}}'
```

### IAM Permissions

**Principle of Least Privilege:**

```yaml
LambdaExecutionPolicy:
  PolicyDocument:
    Statement:
      - Effect: Allow
        Action:
          - logs:CreateLogGroup
          - logs:CreateLogStream
          - logs:PutLogEvents
        Resource: !Sub 'arn:aws:logs:${AWS::Region}:${AWS::AccountId}:*'
```

### API Gateway Security

**Add API key authentication:**

```yaml
ApiKey:
  Type: AWS::ApiGatewayV2::ApiKey
  Properties:
    Name: kairos-api-key

UsagePlan:
  Type: AWS::ApiGatewayV2::UsagePlan
  Properties:
    ApiId: !Ref ApiGateway
    Throttle:
      RateLimit: 1000
      BurstLimit: 2000
```

**Add WAF (Web Application Firewall):**

```yaml
WebACL:
  Type: AWS::WAFv2::WebACL
  Properties:
    Scope: REGIONAL
    Rules:
      - Name: RateLimitRule
        Priority: 1
        Statement:
          RateBasedStatement:
            Limit: 2000
            AggregateKeyType: IP
        Action:
          Block: {}
```

## Troubleshooting

### Common Deployment Issues

#### 1. CloudFormation Stack Failure

**Problem:** Stack creation/update fails

**Diagnosis:**
```bash
# Check stack events
aws cloudformation describe-stack-events \
  --stack-name kairos-backend

# Check stack status
aws cloudformation describe-stacks \
  --stack-name kairos-backend \
  --query 'Stacks[0].StackStatus'
```

**Common Causes:**
- Insufficient IAM permissions
- Invalid parameter values
- Resource conflicts

**Solution:**
```bash
# Delete failed stack
aws cloudformation delete-stack --stack-name kairos-backend

# Fix issues in template.yaml or parameters
# Redeploy
```

#### 2. Lambda Function Errors

**Problem:** Lambda returns 5xx errors

**Diagnosis:**
```bash
# View logs
aws logs tail /aws/lambda/kairos-backend --follow

# Get recent errors
aws logs filter-log-events \
  --log-group-name /aws/lambda/kairos-backend \
  --filter-pattern "ERROR" \
  --max-items 10
```

**Common Causes:**
- MongoDB connection timeout
- Missing environment variables
- Import errors

**Solution:**
- Check environment variables in Lambda console
- Verify MongoDB network access (IP whitelist)
- Check CloudWatch logs for stack traces

#### 3. API Gateway 502/504 Errors

**Problem:** API Gateway returns bad gateway errors

**Diagnosis:**
```bash
# Check Lambda metrics
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=kairos-backend \
  --start-time $(date -u -d '10 minutes ago' +%s) \
  --end-time $(date -u +%s) \
  --period 60 \
  --statistics Sum
```

**Common Causes:**
- Lambda timeout (>15s)
- Lambda execution errors
- Cold start issues

**Solution:**
- Increase Lambda timeout (max 30s for API Gateway)
- Optimize Lambda code
- Consider provisioned concurrency

#### 4. ECR Push Failures

**Problem:** Cannot push image to ECR

**Diagnosis:**
```bash
# Check ECR repository exists
aws ecr describe-repositories --repository-names kairos

# Check authentication
aws ecr get-login-password --region eu-west-2
```

**Common Causes:**
- Not logged in to ECR
- Repository doesn't exist
- Incorrect region

**Solution:**
```bash
# Login to ECR
aws ecr get-login-password --region eu-west-2 | \
  docker login --username AWS --password-stdin \
  $AWS_ACCOUNT_ID.dkr.ecr.eu-west-2.amazonaws.com

# Create repository if needed
aws ecr create-repository --repository-name kairos
```

### Debug Mode

Enable debug logging in Lambda:

```python
# In kairos/main.py
import logging

if settings.ENVIRONMENT != "local":
    logging.basicConfig(level=logging.DEBUG)
```

### Performance Profiling

Profile Lambda execution:

```python
import time

def timed_function():
    start = time.time()
    # ... function code
    duration = time.time() - start
    print(f"Function took {duration:.2f}s")
```