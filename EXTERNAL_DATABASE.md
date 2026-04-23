# Menggunakan PostgreSQL Eksternal

Panduan untuk menggunakan PostgreSQL yang sudah ada (eksternal) dengan aplikasi Docker.

## Skenario

Anda sudah memiliki PostgreSQL yang berjalan di:
- Host machine (localhost)
- Server terpisah
- Docker container lain
- Cloud database (AWS RDS, Google Cloud SQL, dll)

## Setup

### 1. Gunakan Docker Compose untuk Database Eksternal

```bash
# Gunakan file docker-compose khusus
docker-compose -f docker-compose.external-db.yml up -d
```

### 2. Konfigurasi Environment

```bash
# Copy template
cp .env.external-db .env

# Edit .env
nano .env
```

### 3. Sesuaikan DATABASE_URL

Format connection string:
```
postgresql://username:password@host:port/database
```

#### Contoh Konfigurasi

**PostgreSQL di Host Machine (Windows/Mac/Linux):**
```env
DATABASE_URL=postgresql://postgres:qwert12345!@host.docker.internal:5433/satu_data_db
```

**PostgreSQL di Server Lain:**
```env
DATABASE_URL=postgresql://postgres:password@192.168.1.100:5432/satu_data_db
```

**PostgreSQL di Docker Container Lain:**
```env
# Jika di network yang sama
DATABASE_URL=postgresql://postgres:password@postgres-container:5432/satu_data_db

# Atau tambahkan ke docker-compose.external-db.yml:
services:
  api:
    external_links:
      - postgres-container:postgres
```

**Cloud Database:**
```env
# AWS RDS
DATABASE_URL=postgresql://username:password@mydb.abc123.us-east-1.rds.amazonaws.com:5432/satu_data_db

# Google Cloud SQL
DATABASE_URL=postgresql://username:password@34.123.45.67:5432/satu_data_db
```

## Persiapan Database

### 1. Pastikan Database Sudah Ada

```sql
-- Connect ke PostgreSQL
psql -U postgres -h localhost -p 5433

-- Buat database jika belum ada
CREATE DATABASE satu_data_db;

-- Aktifkan pgvector extension
\c satu_data_db
CREATE EXTENSION IF NOT EXISTS vector;
```

### 2. Jalankan Migrations

**Option A: Manual dari Host**
```bash
cd api
psql -U postgres -h localhost -p 5433 -d satu_data_db -f migrations/001_create_chat_tables.sql
psql -U postgres -h localhost -p 5433 -d satu_data_db -f migrations/002_add_embeddings.sql
```

**Option B: Dari Docker Container**
```bash
# Start API container
docker-compose -f docker-compose.external-db.yml up -d api

# Run migrations
docker exec -it chatbot-api python scripts/run_migration.py
```

### 3. Generate Embeddings (Opsional)

```bash
# Dari host
cd api
python scripts/generate_embeddings.py

# Atau dari container
docker exec -it chatbot-api python scripts/generate_embeddings.py
```

## Troubleshooting

### Error: Connection Refused

**Masalah**: Container tidak bisa connect ke database di host.

**Solusi**:
1. Gunakan `host.docker.internal` bukan `localhost`
2. Pastikan PostgreSQL listen ke semua interface:
   ```bash
   # Edit postgresql.conf
   listen_addresses = '*'
   ```
3. Pastikan firewall allow connection dari Docker

### Error: Password Authentication Failed

**Masalah**: Username/password salah atau tidak ada akses.

**Solusi**:
1. Cek credentials di .env
2. Pastikan user punya akses ke database:
   ```sql
   GRANT ALL PRIVILEGES ON DATABASE satu_data_db TO postgres;
   ```
3. Cek pg_hba.conf untuk allow connection

### Error: Database Does Not Exist

**Masalah**: Database belum dibuat.

**Solusi**:
```sql
CREATE DATABASE satu_data_db;
```

### Error: Extension "vector" Does Not Exist

**Masalah**: pgvector extension belum terinstall.

**Solusi**:
```bash
# Install pgvector
# Ubuntu/Debian
sudo apt install postgresql-16-pgvector

# Atau compile from source
git clone https://github.com/pgvector/pgvector.git
cd pgvector
make
sudo make install

# Aktifkan extension
psql -U postgres -d satu_data_db -c "CREATE EXTENSION vector;"
```

## Network Configuration

### Jika PostgreSQL di Docker Network Lain

Edit `docker-compose.external-db.yml`:

```yaml
services:
  api:
    networks:
      - chatbot-network
      - postgres-network  # Network PostgreSQL Anda

networks:
  chatbot-network:
    driver: bridge
  postgres-network:
    external: true  # Network yang sudah ada
```

### Jika Perlu Custom DNS

```yaml
services:
  api:
    extra_hosts:
      - "mydb.local:192.168.1.100"
    environment:
      DATABASE_URL: postgresql://postgres:password@mydb.local:5432/satu_data_db
```

## Security Best Practices

### 1. Gunakan Environment Variables

Jangan hardcode credentials di docker-compose.yml:

```yaml
environment:
  DATABASE_URL: ${DATABASE_URL}  # Dari .env file
```

### 2. Gunakan Docker Secrets (Production)

```yaml
services:
  api:
    secrets:
      - db_url
    environment:
      DATABASE_URL_FILE: /run/secrets/db_url

secrets:
  db_url:
    file: ./secrets/db_url.txt
```

### 3. Restrict Database Access

```sql
-- Buat user khusus untuk aplikasi
CREATE USER chatbot_app WITH PASSWORD 'strong_password';
GRANT CONNECT ON DATABASE satu_data_db TO chatbot_app;
GRANT USAGE ON SCHEMA public TO chatbot_app;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO chatbot_app;
```

### 4. Use SSL Connection

```env
DATABASE_URL=postgresql://user:pass@host:5432/db?sslmode=require
```

## Testing Connection

### Test dari Host

```bash
# Test connection
psql "postgresql://postgres:qwert12345!@localhost:5433/satu_data_db" -c "SELECT version();"
```

### Test dari Container

```bash
# Start container
docker-compose -f docker-compose.external-db.yml up -d api

# Test connection
docker exec -it chatbot-api python -c "
from sqlalchemy import create_engine
import os
engine = create_engine(os.getenv('DATABASE_URL'))
with engine.connect() as conn:
    result = conn.execute('SELECT version()')
    print(result.fetchone())
"
```

## Monitoring

### Check Connections

```sql
-- Lihat active connections
SELECT 
    datname,
    usename,
    application_name,
    client_addr,
    state,
    query
FROM pg_stat_activity
WHERE datname = 'satu_data_db';
```

### Check Logs

```bash
# API logs
docker-compose -f docker-compose.external-db.yml logs -f api

# PostgreSQL logs (tergantung setup)
tail -f /var/log/postgresql/postgresql-16-main.log
```

## Backup & Restore

### Backup

```bash
# Backup database
pg_dump -U postgres -h localhost -p 5433 satu_data_db > backup_$(date +%Y%m%d).sql

# Backup dengan compression
pg_dump -U postgres -h localhost -p 5433 satu_data_db | gzip > backup_$(date +%Y%m%d).sql.gz
```

### Restore

```bash
# Restore dari backup
psql -U postgres -h localhost -p 5433 satu_data_db < backup_20240423.sql

# Restore dari compressed backup
gunzip -c backup_20240423.sql.gz | psql -U postgres -h localhost -p 5433 satu_data_db
```

## Migration dari Docker PostgreSQL ke Eksternal

Jika Anda sudah menggunakan PostgreSQL di Docker dan ingin pindah ke eksternal:

### 1. Backup Data dari Docker

```bash
# Backup dari container
docker exec chatbot-postgres pg_dump -U postgres satu_data_db > backup.sql
```

### 2. Restore ke Database Eksternal

```bash
# Restore ke database eksternal
psql -U postgres -h localhost -p 5433 satu_data_db < backup.sql
```

### 3. Update Configuration

```bash
# Update .env
cp .env.external-db .env
# Edit DATABASE_URL

# Restart dengan config baru
docker-compose -f docker-compose.external-db.yml up -d
```

### 4. Cleanup (Opsional)

```bash
# Stop dan hapus container PostgreSQL lama
docker-compose down postgres
docker volume rm ldt_chatbot_postgres_data
```

## Performance Tuning

### Connection Pooling

API sudah menggunakan SQLAlchemy connection pooling. Sesuaikan di `api/app/config.py`:

```python
DB_POOL_SIZE: int = 20
DB_MAX_OVERFLOW: int = 40
```

### PostgreSQL Configuration

Untuk production, sesuaikan postgresql.conf:

```conf
max_connections = 200
shared_buffers = 256MB
effective_cache_size = 1GB
work_mem = 4MB
maintenance_work_mem = 64MB
```

## Support

Untuk bantuan lebih lanjut:
- Check logs: `docker-compose -f docker-compose.external-db.yml logs -f`
- Test connection: Lihat section "Testing Connection"
- PostgreSQL docs: https://www.postgresql.org/docs/
- pgvector docs: https://github.com/pgvector/pgvector
