# Docker Usage Guide

Panduan singkat menggunakan Docker untuk deployment.

## Quick Start

### Option 1: Dengan PostgreSQL di Docker (Recommended untuk Development)

```bash
# Copy environment file
cp .env.docker .env

# Start semua services termasuk PostgreSQL
docker-compose --profile with-postgres up -d

# Atau lebih singkat
COMPOSE_PROFILES=with-postgres docker-compose up -d
```

### Option 2: Dengan PostgreSQL Eksternal (Untuk Production)

Jika Anda sudah punya PostgreSQL yang berjalan:

```bash
# Copy environment file
cp .env.docker .env

# Edit .env dan set DATABASE_URL ke PostgreSQL Anda
nano .env
```

Edit `.env`:
```env
# Contoh untuk PostgreSQL di host machine
DATABASE_URL=postgresql://postgres:qwert12345!@host.docker.internal:5433/satu_data_db

# Atau PostgreSQL di server lain
# DATABASE_URL=postgresql://postgres:password@192.168.1.100:5432/satu_data_db
```

```bash
# Start tanpa PostgreSQL container
docker-compose up -d
```

## Akses Aplikasi

- **Frontend**: http://localhost:8766/chatbot/
- **API Docs**: http://localhost:8765/chatbot-api/docs
- **Health Check**: http://localhost:8765/chatbot-api/health

## Commands

```bash
# Start services
docker-compose up -d

# Start dengan PostgreSQL
docker-compose --profile with-postgres up -d

# View logs
docker-compose logs -f

# View logs untuk service tertentu
docker-compose logs -f api

# Stop services
docker-compose down

# Stop dan hapus volumes (WARNING: hapus data PostgreSQL)
docker-compose down -v

# Rebuild services
docker-compose up -d --build

# Check status
docker-compose ps

# Restart service tertentu
docker-compose restart api
```

## Environment Variables

Edit file `.env`:

```env
# Database (pilih salah satu)
# Option 1: Gunakan default (postgres container)
# Tidak perlu set DATABASE_URL

# Option 2: Gunakan PostgreSQL eksternal
DATABASE_URL=postgresql://user:pass@host:port/database

# Qwen API
QWEN_API_URL=http://host.docker.internal:9002/v1/chat/completions

# Maintenance Mode
MAINTENANCE_MODE=false
MAINTENANCE_MESSAGE=Sistem sedang dalam pemeliharaan
MAINTENANCE_ETA=2 jam
```

## Troubleshooting

### PostgreSQL Container Tidak Start

```bash
# Check logs
docker-compose logs postgres

# Check if port 5433 is already in use
netstat -tulpn | grep 5433

# Change port in docker-compose.yml if needed
```

### API Tidak Bisa Connect ke Database

**Jika menggunakan PostgreSQL di Docker:**
```bash
# Pastikan postgres container running
docker-compose ps postgres

# Check DATABASE_URL di .env (harus kosong atau comment)
```

**Jika menggunakan PostgreSQL eksternal:**
```bash
# Test connection dari host
psql "postgresql://postgres:password@localhost:5433/satu_data_db" -c "SELECT 1;"

# Pastikan DATABASE_URL di .env sudah benar
# Gunakan host.docker.internal untuk PostgreSQL di host machine
```

### Frontend Tidak Bisa Connect ke API

```bash
# Check API is running
curl http://localhost:8765/chatbot-api/health

# Check CORS settings
docker-compose logs api | grep CORS

# Rebuild frontend
docker-compose up -d --build frontend
```

## Database Management

### Backup Database (PostgreSQL di Docker)

```bash
# Backup
docker exec chatbot-postgres pg_dump -U postgres satu_data_db > backup_$(date +%Y%m%d).sql

# Restore
docker exec -i chatbot-postgres psql -U postgres satu_data_db < backup_20240423.sql
```

### Access Database

```bash
# Via psql
docker exec -it chatbot-postgres psql -U postgres -d satu_data_db

# Via external tool (DBeaver, pgAdmin, etc.)
# Host: localhost
# Port: 5433
# Database: satu_data_db
# User: postgres
# Password: qwert12345!
```

## Production Deployment

### 1. Update Environment

```bash
# .env
DATABASE_URL=postgresql://user:pass@production-db:5432/satu_data_db
QWEN_API_URL=http://production-qwen:9002/v1/chat/completions
MAINTENANCE_MODE=false

# frontend/.env.production
VITE_API_BASE_URL=https://yourdomain.com/chatbot-api
VITE_MAINTENANCE_MODE=false
VITE_SHOW_ERROR_DETAILS=false
```

### 2. Use Production Compose

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  api:
    environment:
      LOG_LEVEL: WARNING
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

  frontend:
    deploy:
      resources:
        limits:
          cpus: '0.5'
          memory: 512M
```

Run:
```bash
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

### 3. Setup Reverse Proxy

See [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) for Nginx configuration.

## Monitoring

```bash
# Resource usage
docker stats

# Health checks
docker-compose ps

# API health
curl http://localhost:8765/chatbot-api/health

# Frontend health
curl http://localhost:8766/chatbot/
```

## Cleanup

```bash
# Stop all services
docker-compose down

# Remove volumes (WARNING: deletes data)
docker-compose down -v

# Remove images
docker-compose down --rmi all

# Full cleanup
docker system prune -a --volumes
```

## Support

- Full documentation: [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)
- External database guide: [EXTERNAL_DATABASE.md](EXTERNAL_DATABASE.md)
- Error handling: [ERROR_HANDLING.md](ERROR_HANDLING.md)
