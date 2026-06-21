# DEPLOY.md — Step-by-Step Deploy Guide

## Prerequisites
- AWS CLI configured (`aws configure`)
- Docker Desktop running
- SAM CLI installed (`sam --version`)
- Node.js 20 installed

---

## Step 1 — Create ECR repositories (once only)

```bash
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=us-east-1

for svc in product-catalogue cart order user-auth search; do
  aws ecr create-repository --repository-name retail/$svc --region $AWS_REGION
done
echo "ECR repos created"
```

---

## Step 2 — Build and push Docker images

```bash
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)
AWS_REGION=us-east-1
ECR=$AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com

# Login to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR

# Build and push each service
for svc in product-catalogue cart order user-auth search; do
  echo "Building $svc..."
  docker build -t $ECR/retail/$svc:latest ./services/$svc
  docker push $ECR/retail/$svc:latest
done
echo "All images pushed"
```

---

## Step 3 — Store JWT secret in SSM

```bash
aws ssm put-parameter \
  --name /retail/jwt-secret \
  --value "$(openssl rand -base64 32)" \
  --type SecureString \
  --region us-east-1
```

---

## Step 4 — Deploy infrastructure with SAM

```bash
cd infra
sam deploy \
  --template-file template.yaml \
  --stack-name retail-platform \
  --capabilities CAPABILITY_IAM CAPABILITY_NAMED_IAM \
  --region us-east-1 \
  --resolve-s3

# Note the outputs — you'll need the App Runner service URLs
```

---

## Step 5 — Seed DynamoDB with product data

```bash
cd infra
pip install boto3 requests
python seed.py --aws
```

---

## Step 6 — Deploy React frontend

```bash
# Create S3 bucket
BUCKET=retail-frontend-$(aws sts get-caller-identity --query Account --output text)
aws s3 mb s3://$BUCKET --region us-east-1

# Get API Gateway URL from SAM outputs and set it
API_URL="https://YOUR-API-GATEWAY-URL"

# Build frontend
cd frontend
npm install
VITE_API_URL=$API_URL npm run build

# Deploy to S3
aws s3 sync dist/ s3://$BUCKET --delete

# Create CloudFront distribution
aws cloudfront create-distribution \
  --origin-domain-name $BUCKET.s3.amazonaws.com \
  --default-root-object index.html \
  --query 'Distribution.DomainName' --output text
```

---

## Step 7 — Set GitHub Secrets (for auto-deploy)

In your GitHub repo → Settings → Secrets → Actions, add:

| Secret | Value |
|---|---|
| `AWS_ACCOUNT_ID` | Your 12-digit AWS account ID |
| `AWS_DEPLOY_ROLE_ARN` | IAM role ARN (see Step 8) |
| `APPRUNNER_ARN_product-catalogue` | App Runner service ARN from SAM output |
| `APPRUNNER_ARN_cart` | App Runner service ARN |
| `APPRUNNER_ARN_order` | App Runner service ARN |
| `APPRUNNER_ARN_user-auth` | App Runner service ARN |
| `APPRUNNER_ARN_search` | App Runner service ARN |
| `FRONTEND_BUCKET` | S3 bucket name |
| `CLOUDFRONT_DIST_ID` | CloudFront distribution ID |
| `API_GATEWAY_URL` | API Gateway URL |

---

## Step 8 — Create OIDC role for GitHub Actions (once only)

```bash
AWS_ACCOUNT=$(aws sts get-caller-identity --query Account --output text)

# Create OIDC provider for GitHub
aws iam create-open-id-connect-provider \
  --url https://token.actions.githubusercontent.com \
  --client-id-list sts.amazonaws.com \
  --thumbprint-list 6938fd4d98bab03faadb97b34396831e3780aea1

# Create trust policy
cat > /tmp/trust.json << TRUST
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": {"Federated": "arn:aws:iam::${AWS_ACCOUNT}:oidc-provider/token.actions.githubusercontent.com"},
    "Action": "sts:AssumeRoleWithWebIdentity",
    "Condition": {
      "StringEquals": {"token.actions.githubusercontent.com:aud": "sts.amazonaws.com"},
      "StringLike": {"token.actions.githubusercontent.com:sub": "repo:PrasenjitRoychoudhury/MyRetailAILDC:*"}
    }
  }]
}
TRUST

# Create the role
aws iam create-role \
  --role-name retail-github-deploy-role \
  --assume-role-policy-document file:///tmp/trust.json

# Attach permissions
aws iam attach-role-policy \
  --role-name retail-github-deploy-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonEC2ContainerRegistryPowerUser

aws iam attach-role-policy \
  --role-name retail-github-deploy-role \
  --policy-arn arn:aws:iam::aws:policy/AWSAppRunnerFullAccess

aws iam attach-role-policy \
  --role-name retail-github-deploy-role \
  --policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess

aws iam attach-role-policy \
  --role-name retail-github-deploy-role \
  --policy-arn arn:aws:iam::aws:policy/CloudFrontFullAccess

echo "Role ARN: arn:aws:iam::${AWS_ACCOUNT}:role/retail-github-deploy-role"
```

---

## Step 9 — Test locally first

```bash
# Start everything locally
docker-compose up -d

# Seed local DynamoDB
cd infra && python seed.py --local

# Open frontend
cd frontend && npm install && npm run dev
# → open http://localhost:5173
```

---

## Auto-deploy from now on

Once Steps 1–8 are done, every `git push origin main` will:
1. Run tests (CI)
2. Build Docker images
3. Push to ECR
4. Update App Runner services
5. Build and deploy React to S3
6. Invalidate CloudFront cache

**No manual steps ever again.**
