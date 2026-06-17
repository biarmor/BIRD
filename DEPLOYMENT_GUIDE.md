# BIRD Backend Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the BIRD multi-agent system to production environments.

## Prerequisites

- Python 3.9+
- SQLite or PostgreSQL database
- Ollama (for local LLM inference)
- Docker (optional, for containerized deployment)
- 4GB+ RAM recommended
- 10GB+ disk space for models

## Local Development Setup

### 1. Clone Repository

```bash
git clone https://github.com/bird-system/bird-backend.git
cd bird-backend
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your configuration:

```env
# Database
DATABASE_URL=sqlite:///./bird.db

# Security
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60

# Ollama
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=qwen2:14b

# API
API_HOST=0.0.0.0
API_PORT=8000
DEBUG=False
```

### 5. Initialize Database

```bash
python3 -m app.database
```

### 6. Start Development Server

```bash
python3 -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at `http://localhost:8000`

## Production Deployment

### Docker Deployment

#### 1. Create Dockerfile

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Create database directory
RUN mkdir -p /app/data

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health')"

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

#### 2. Build Docker Image

```bash
docker build -t bird-backend:latest .
```

#### 3. Run Docker Container

```bash
docker run -d \
  --name bird-backend \
  -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./data/bird.db \
  -e SECRET_KEY=your-secret-key \
  -v bird-data:/app/data \
  bird-backend:latest
```

### Kubernetes Deployment

#### 1. Create Deployment Manifest

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: bird-backend
  namespace: bird-system
spec:
  replicas: 3
  selector:
    matchLabels:
      app: bird-backend
  template:
    metadata:
      labels:
        app: bird-backend
    spec:
      containers:
      - name: bird-backend
        image: bird-backend:latest
        ports:
        - containerPort: 8000
        env:
        - name: DATABASE_URL
          valueFrom:
            secretKeyRef:
              name: bird-secrets
              key: database-url
        - name: SECRET_KEY
          valueFrom:
            secretKeyRef:
              name: bird-secrets
              key: secret-key
        resources:
          requests:
            memory: "512Mi"
            cpu: "500m"
          limits:
            memory: "1Gi"
            cpu: "1000m"
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 5
          periodSeconds: 5
---
apiVersion: v1
kind: Service
metadata:
  name: bird-backend-service
  namespace: bird-system
spec:
  selector:
    app: bird-backend
  ports:
  - protocol: TCP
    port: 80
    targetPort: 8000
  type: LoadBalancer
```

#### 2. Deploy to Kubernetes

```bash
kubectl apply -f deployment.yaml
```

### Cloud Platform Deployment

#### AWS EC2

```bash
# Launch EC2 instance
aws ec2 run-instances \
  --image-id ami-0c55b159cbfafe1f0 \
  --instance-type t3.medium \
  --key-name my-key-pair

# SSH into instance
ssh -i my-key-pair.pem ec2-user@<instance-ip>

# Install dependencies
sudo yum install python3 python3-pip git
git clone https://github.com/bird-system/bird-backend.git
cd bird-backend

# Setup and run
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
python3 -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### Google Cloud Run

```bash
# Build and push image
gcloud builds submit --tag gcr.io/PROJECT_ID/bird-backend

# Deploy
gcloud run deploy bird-backend \
  --image gcr.io/PROJECT_ID/bird-backend \
  --platform managed \
  --region us-central1 \
  --memory 1Gi \
  --set-env-vars DATABASE_URL=postgresql://...
```

#### Azure App Service

```bash
# Create resource group
az group create --name bird-rg --location eastus

# Create App Service Plan
az appservice plan create \
  --name bird-plan \
  --resource-group bird-rg \
  --sku B2

# Create Web App
az webapp create \
  --resource-group bird-rg \
  --plan bird-plan \
  --name bird-backend

# Deploy from GitHub
az webapp deployment source config-zip \
  --resource-group bird-rg \
  --name bird-backend \
  --src deployment.zip
```

## Database Configuration

### SQLite (Development)

```env
DATABASE_URL=sqlite:///./bird.db
```

### PostgreSQL (Production)

```env
DATABASE_URL=postgresql://user:password@localhost:5432/bird
```

#### Setup PostgreSQL

```bash
# Install PostgreSQL
sudo apt-get install postgresql postgresql-contrib

# Create database and user
sudo -u postgres psql
CREATE DATABASE bird;
CREATE USER bird_user WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE bird TO bird_user;
\q

# Update .env
DATABASE_URL=postgresql://bird_user:secure_password@localhost:5432/bird
```

### MySQL (Production)

```env
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/bird
```

## Ollama Integration

### Local Ollama Setup

```bash
# Install Ollama
curl https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# In another terminal, pull models
ollama pull qwen2:14b
ollama pull qwen2:7b
ollama pull mistral:7b
```

### Remote Ollama

```env
OLLAMA_BASE_URL=http://ollama-server:11434
OLLAMA_MODEL=qwen2:14b
```

## Security Configuration

### 1. Generate Secret Key

```python
import secrets
secret_key = secrets.token_urlsafe(32)
print(secret_key)
```

### 2. SSL/TLS Certificate

```bash
# Generate self-signed certificate
openssl req -x509 -newkey rsa:4096 -nodes -out cert.pem -keyout key.pem -days 365

# Update .env
SSL_CERT_FILE=cert.pem
SSL_KEY_FILE=key.pem
```

### 3. Environment Variables

Never commit `.env` to version control:

```bash
echo ".env" >> .gitignore
```

### 4. Firewall Configuration

```bash
# UFW (Ubuntu)
sudo ufw allow 8000/tcp
sudo ufw allow 5432/tcp
sudo ufw enable
```

## Monitoring and Logging

### Application Logging

```python
# Configured in app/main.py
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/bird.log'),
        logging.StreamHandler()
    ]
)
```

### Health Check Endpoint

```bash
curl http://localhost:8000/health
```

### Prometheus Metrics

```bash
# Access metrics
curl http://localhost:8000/metrics
```

### Log Aggregation

```yaml
# Docker Compose with ELK Stack
version: '3'
services:
  bird-backend:
    image: bird-backend:latest
    logging:
      driver: "splunk"
      options:
        splunk-token: "your-token"
        splunk-url: "https://your-splunk-instance:8088"
```

## Performance Tuning

### Database Optimization

```sql
-- Create indices
CREATE INDEX idx_vault_facts_category ON vault_facts(category);
CREATE INDEX idx_vault_facts_embedding ON vault_facts(embedding);
CREATE INDEX idx_intelligence_queries_workspace ON intelligence_queries(workspace_id);
```

### Connection Pooling

```python
# In config/settings.py
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_MAX_OVERFLOW = 40
SQLALCHEMY_POOL_RECYCLE = 3600
```

### Caching

```python
# Redis caching
REDIS_URL = "redis://localhost:6379/0"
CACHE_TTL = 3600  # 1 hour
```

## Backup and Recovery

### Database Backup

```bash
# SQLite
cp bird.db bird.db.backup

# PostgreSQL
pg_dump -U bird_user bird > bird_backup.sql

# Restore
psql -U bird_user bird < bird_backup.sql
```

### Automated Backups

```bash
# Create backup script
#!/bin/bash
BACKUP_DIR="/backups/bird"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)

mkdir -p $BACKUP_DIR
pg_dump -U bird_user bird | gzip > $BACKUP_DIR/bird_$TIMESTAMP.sql.gz

# Keep only last 30 days
find $BACKUP_DIR -mtime +30 -delete
```

### Disaster Recovery

```bash
# Restore from backup
gunzip < /backups/bird/bird_20260617_120000.sql.gz | psql -U bird_user bird
```

## Troubleshooting

### Common Issues

**Issue: Database connection failed**
```bash
# Check database is running
sudo systemctl status postgresql

# Verify connection string
python3 -c "from sqlalchemy import create_engine; engine = create_engine('postgresql://...')"
```

**Issue: Ollama model not found**
```bash
# List available models
ollama list

# Pull required model
ollama pull qwen2:14b
```

**Issue: High memory usage**
```bash
# Monitor memory
free -h
ps aux | grep python

# Reduce pool size in config
SQLALCHEMY_POOL_SIZE = 10
```

**Issue: Slow API responses**
```bash
# Check database performance
EXPLAIN ANALYZE SELECT * FROM vault_facts;

# Add indices if needed
CREATE INDEX idx_vault_facts_category ON vault_facts(category);
```

## Maintenance

### Regular Tasks

- **Daily**: Monitor logs and error rates
- **Weekly**: Check database size and performance
- **Monthly**: Review and optimize slow queries
- **Quarterly**: Update dependencies and security patches

### Dependency Updates

```bash
# Check for updates
pip list --outdated

# Update specific package
pip install --upgrade fastapi

# Update all
pip install --upgrade -r requirements.txt
```

### Database Maintenance

```bash
# PostgreSQL maintenance
VACUUM ANALYZE;
REINDEX DATABASE bird;
```

## Scaling

### Horizontal Scaling

```yaml
# Docker Compose with multiple instances
version: '3'
services:
  bird-backend-1:
    image: bird-backend:latest
    ports:
      - "8001:8000"
  bird-backend-2:
    image: bird-backend:latest
    ports:
      - "8002:8000"
  
  nginx:
    image: nginx:latest
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### Load Balancing

```nginx
# nginx.conf
upstream bird_backend {
    server bird-backend-1:8000;
    server bird-backend-2:8000;
    server bird-backend-3:8000;
}

server {
    listen 80;
    location / {
        proxy_pass http://bird_backend;
    }
}
```

## Support and Documentation

- **Documentation**: https://docs.bird.local
- **Issues**: https://github.com/bird-system/issues
- **Community**: https://community.bird.local
- **Email**: support@bird.local
