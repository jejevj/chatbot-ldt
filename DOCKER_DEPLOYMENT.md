# Docker Deployment Guide

Panduan lengkap untuk deploy aplikasi Chatbot Satu Data Pertahanan menggunakan Docker.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- Minimal 4GB RAM
- Minimal 10GB disk space

## Port Configuration

Aplikasi menggunakan port yang jarang digunakan untuk menghindari konflik:

- **Frontend**: `8766`
- **Backend API**: `8765`
- **PostgreSQL**: `5433` (mapped dari 5432 di container)

## Quick Start

### 1. Clone Repository

```bash
git clone <repository-url>
cd ldt_chatbot
```

### 2. Setup Environment

```bash
# Copy environment file
cp .env.docker .env

# Edit .env jika perlu
nano .env
```

### 3. Build dan Run

```bash
# Build dan start semua services
docker-compose up -d

# Atau build ulang jika ada perubahan
docker-compose up -d --build
```

### 4. Akses Aplikasi

- Frontend: http://localhost:8766/chatbot/
- API Docs: http://localhost:8765/chatbot-api/docs
- Health Check: http://localhost:8765/chatbot-api/health

## Architecture

```
┌─────────────────┐
│   Frontend      │
│   (Nginx)       │
│   Port: 8766    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Backend API   │
│   (FastAPI)     │
│   Port: 8765    │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   PostgreSQL    │
│   (pgvector)    │
│   Port: 5433    │
└─────────────────┘
```

## Services

### 1. PostgreSQL (postgres)

Database dengan pgvector extension untuk vector similarity search.

**Container**: `chatbot-postgres`
**Image**: `pgvector/pgvector:pg16`
**Port**: `5433:5432`

**Environment Variables**:
- `POSTGRES_DB`: satu_data_db
- `POSTGRES_USER`: postgres
- `POSTGRES_PASSWORD`: qwert12345!

**Volumes**:
- `postgres_data`: Persistent database storage
- `./api/migrations`: SQL migration files

### 2. Backend API (api)

FastAPI application dengan RAG capabilities.

**Container**: `chatbot-api`
**Port**: `8765:8765`

**Environment Variables**:
- `DATABASE_URL`: Connection string ke PostgreSQL
- `QWEN_API_URL`: URL ke Qwen LLM API
- `QWEN_MODEL`: Model name
- `CORS_ORIGINS`: Allowed origins
- `MAINTENANCE_MODE`: Enable/disable maintenance

**Dependencies**: postgres (healthy)

### 3. Frontend (frontend)

Vue.js SPA served by Nginx.

**Container**: `chatbot-frontend`
**Port**: `8766:8766`

**Build Args**:
- `VITE_API_BASE_URL`: Backend API URL

**Dependencies**: api

## Docker Commands

### Start Services

```bash
# Start all services
docker-compose up -d

# Start specific service
docker-compose up -d api

# View logs
docker-compose logs -f

# View logs for specific service
docker-compose logs -f api
```

### Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (WARNING: deletes database)
docker-compose down -v
```

### Rebuild Services

```bash
# Rebuild all
docker-compose up -d --build

# Rebuild specific service
docker-compose up -d --build api
```

### Check Status

```bash
# List running containers
docker-compose ps

# Check health
docker-compose ps
```

### Access Container Shell

```bash
# API container
docker exec -it chatbot-api bash

# Frontend container
docker exec -it chatbot-frontend sh

# Database container
docker exec -it chatbot-postgres psql -U postgres -d satu_data_db
```

## Database Management

### Run Migrations

Migrations run automatically on first start. To run manually:

```bash
docker exec -it chatbot-postgres psql -U postgres -d satu_data_db -f /docker-entrypoint-initdb.d/001_create_chat_tables.sql
docker exec -it chatbot-postgres psql -U postgres -d satu_data_db -f /docker-entrypoint-initdb.d/002_add_embeddings.sql
```

### Backup Database

```bash
# Create backup
docker exec chatbot-postgres pg_dump -U postgres satu_data_db > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore backup
docker exec -i chatbot-postgres psql -U postgres satu_data_db < backup_20240423_120000.sql
```

### Access Database

```bash
# Using psql
docker exec -it chatbot-postgres psql -U postgres -d satu_data_db

# Using external tool (e.g., DBeaver, pgAdmin)
# Host: localhost
# Port: 5433
# Database: satu_data_db
# User: postgres
# Password: qwert12345!
```

## Qwen LLM Integration

Aplikasi membutuhkan Qwen LLM API yang berjalan di host machine atau server terpisah.

### Option 1: Qwen di Host Machine

```bash
# Di .env
QWEN_API_URL=http://host.docker.internal:9002/v1/chat/completions
```

### Option 2: Qwen di Server Terpisah

```bash
# Di .env
QWEN_API_URL=http://your-qwen-server:9002/v1/chat/completions
```

### Option 3: Qwen di Docker (Advanced)

Tambahkan service di `docker-compose.yml`:

```yaml
qwen:
  image: your-qwen-image
  container_name: chatbot-qwen
  ports:
    - "9002:9002"
  networks:
    - chatbot-network
```

Update API environment:
```yaml
QWEN_API_URL: http://qwen:9002/v1/chat/completions
```

## Maintenance Mode

### Enable Maintenance

```bash
# Edit .env
MAINTENANCE_MODE=true
MAINTENANCE_MESSAGE=Sistem sedang dalam pemeliharaan
MAINTENANCE_ETA=2 jam

# Restart API
docker-compose restart api
```

### Disable Maintenance

```bash
# Edit .env
MAINTENANCE_MODE=false

# Restart API
docker-compose restart api
```

## Production Deployment

### 1. Update Environment Variables

```bash
# .env
QWEN_API_URL=http://your-production-qwen:9002/v1/chat/completions
MAINTENANCE_MODE=false

# frontend/.env.production
VITE_API_BASE_URL=https://yourdomain.com/chatbot-api
VITE_MAINTENANCE_MODE=false
VITE_SHOW_ERROR_DETAILS=false
```

### 2. Use Production Compose File

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  api:
    environment:
      LOG_LEVEL: WARNING
      API_RELOAD: false
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 1G

  frontend:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
```

Run with:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 3. Setup Reverse Proxy (Nginx)

```nginx
# /etc/nginx/sites-available/chatbot

upstream chatbot_api {
    server localhost:8765;
}

upstream chatbot_frontend {
    server localhost:8766;
}

server {
    listen 80;
    server_name yourdomain.com;

    # Redirect to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Frontend
    location /chatbot/ {
        proxy_pass http://chatbot_frontend/chatbot/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # API
    location /chatbot-api/ {
        proxy_pass http://chatbot_api/chatbot-api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # WebSocket support (if needed)
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
}
```

### 4. Setup SSL with Let's Encrypt

```bash
# Install certbot
sudo apt install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d yourdomain.com

# Auto-renewal
sudo certbot renew --dry-run
```

## Monitoring

### View Logs

```bash
# All services
docker-compose logs -f

# Specific service with tail
docker-compose logs -f --tail=100 api

# Save logs to file
docker-compose logs > logs_$(date +%Y%m%d_%H%M%S).txt
```

### Resource Usage

```bash
# Container stats
docker stats

# Specific container
docker stats chatbot-api
```

### Health Checks

```bash
# Check all services
docker-compose ps

# API health
curl http://localhost:8765/chatbot-api/health

# Frontend health
curl http://localhost:8766/chatbot/
```

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose logs api

# Check if port is in use
netstat -tulpn | grep 8765

# Remove and recreate
docker-compose down
docker-compose up -d
```

### Database Connection Error

```bash
# Check if postgres is healthy
docker-compose ps postgres

# Check database logs
docker-compose logs postgres

# Test connection
docker exec chatbot-postgres pg_isready -U postgres
```

### Frontend Can't Connect to API

```bash
# Check API is running
curl http://localhost:8765/chatbot-api/health

# Check CORS settings in API
docker-compose logs api | grep CORS

# Rebuild frontend with correct API URL
docker-compose up -d --build frontend
```

### Out of Memory

```bash
# Check memory usage
docker stats

# Increase Docker memory limit in Docker Desktop settings
# Or add memory limits in docker-compose.yml
```

## Scaling

### Horizontal Scaling

```bash
# Scale API instances
docker-compose up -d --scale api=3

# Add load balancer (nginx)
# Update docker-compose.yml with nginx service
```

### Vertical Scaling

Edit `docker-compose.yml`:

```yaml
services:
  api:
    deploy:
      resources:
        limits:
          cpus: '4'
          memory: 4G
```

## Backup & Restore

### Full Backup

```bash
#!/bin/bash
# backup.sh

BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p $BACKUP_DIR

# Backup database
docker exec chatbot-postgres pg_dump -U postgres satu_data_db > $BACKUP_DIR/database.sql

# Backup volumes
docker run --rm -v ldt_chatbot_postgres_data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar czf /backup/postgres_data.tar.gz -C /data .

# Backup logs
cp -r api/logs $BACKUP_DIR/

echo "Backup completed: $BACKUP_DIR"
```

### Restore

```bash
#!/bin/bash
# restore.sh

BACKUP_DIR=$1

# Restore database
docker exec -i chatbot-postgres psql -U postgres satu_data_db < $BACKUP_DIR/database.sql

# Restore volumes
docker run --rm -v ldt_chatbot_postgres_data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar xzf /backup/postgres_data.tar.gz -C /data

echo "Restore completed from: $BACKUP_DIR"
```

## Security Best Practices

1. **Change Default Passwords**
   ```bash
   # Update in docker-compose.yml and .env
   POSTGRES_PASSWORD=your-strong-password
   ```

2. **Use Secrets for Production**
   ```yaml
   services:
     api:
       secrets:
         - db_password
   
   secrets:
     db_password:
       file: ./secrets/db_password.txt
   ```

3. **Limit Network Exposure**
   ```yaml
   services:
     postgres:
       ports: []  # Don't expose to host
   ```

4. **Regular Updates**
   ```bash
   # Update images
   docker-compose pull
   docker-compose up -d
   ```

5. **Enable Firewall**
   ```bash
   # Only allow necessary ports
   sudo ufw allow 80/tcp
   sudo ufw allow 443/tcp
   sudo ufw enable
   ```

## Performance Tuning

### PostgreSQL

Edit `docker-compose.yml`:

```yaml
postgres:
  command: 
    - "postgres"
    - "-c"
    - "shared_buffers=256MB"
    - "-c"
    - "max_connections=200"
    - "-c"
    - "work_mem=4MB"
```

### Nginx Cache

Update `frontend/nginx.conf`:

```nginx
# Add caching
proxy_cache_path /var/cache/nginx levels=1:2 keys_zone=api_cache:10m max_size=100m;

location /chatbot-api/ {
    proxy_cache api_cache;
    proxy_cache_valid 200 5m;
    proxy_cache_use_stale error timeout http_500 http_502 http_503 http_504;
}
```

## Support

Untuk bantuan lebih lanjut:
- Check logs: `docker-compose logs`
- GitHub Issues: [repository-url]/issues
- Documentation: README.md
