# MyRetailAILDC — AI-LDC Retail Platform

A microservice retail website and the base application for the AI-SDLC Factory pipeline.

## Architecture
- **SVC-1** Product Catalogue — FastAPI on AWS App Runner
- **SVC-2** Shopping Cart — FastAPI on AWS App Runner
- **SVC-3** Order Service — FastAPI on AWS App Runner
- **SVC-4** User & Auth — FastAPI on AWS App Runner
- **SVC-5** Search — FastAPI on AWS App Runner
- **Frontend** — React (Vite + Tailwind) on S3 + CloudFront
- **Database** — DynamoDB single table (retail-platform)
- **Events** — EventBridge (retail-events bus)

## Local Development
```bash
# Start all services locally
docker-compose up

# Seed DynamoDB Local with product data
cd infra && python seed.py --local

# Frontend
cd frontend && npm install && npm run dev
```

## Deploy to AWS
```bash
# First time setup
aws configure
cd infra && python setup_aws.py

# Deploy all services
sam build && sam deploy --guided

# Deploy frontend
cd frontend && npm run build
aws s3 sync dist/ s3://YOUR-BUCKET-NAME
```

## CI/CD
Push to `main` → GitHub Actions → ECR → App Runner + S3 (auto).

## Phase 0 Services
| Service | Port (local) | Route |
|---|---|---|
| Product Catalogue | 8001 | /products |
| Cart | 8002 | /cart |
| Order | 8003 | /orders |
| User & Auth | 8004 | /users, /auth |
| Search | 8005 | /search |
