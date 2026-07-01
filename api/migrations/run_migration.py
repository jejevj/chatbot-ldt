"""
Migration script: tambah kolom question_embedding ke t_kemhan_feedback

Cara jalankan di server:
  docker exec -it chatbot-api python3 /app/migrations/run_migration.py

Atau dari host:
  docker exec chatbot-api python3 /app/migrations/run_migration.py
"""
import os
import sys

print("=" * 60)
print("Migration: add question_embedding to t_kemhan_feedback")
print("=" * 60)

try:
    import psycopg2
except ImportError:
    print("[ERROR] psycopg2 tidak tersedia di container ini.")
    print("Gunakan container database:\n")
    print("  docker exec -it chatbot-db psql -U postgres -d chatbot -c \\")
    print("    \"ALTER TABLE t_kemhan_feedback ADD COLUMN IF NOT EXISTS question_embedding vector(384);\"")
    sys.exit(1)

# Ambil DATABASE_URL dari environment (sudah ada di container API)
db_url = os.getenv("DATABASE_URL", "")
if not db_url:
    print("[ERROR] Environment variable DATABASE_URL tidak ditemukan.")
    sys.exit(1)

# Parse DATABASE_URL → psycopg2 connect params
# Format: postgresql://user:pass@host:port/dbname
try:
    from urllib.parse import urlparse
    p = urlparse(db_url)
    conn = psycopg2.connect(
        host=p.hostname,
        port=p.port or 5432,
        dbname=p.path.lstrip("/"),
        user=p.username,
        password=p.password,
    )
    conn.autocommit = True
    cur = conn.cursor()
    print(f"[OK] Terhubung ke database: {p.hostname}/{p.path.lstrip('/')}")
except Exception as e:
    print(f"[ERROR] Gagal koneksi ke database: {e}")
    sys.exit(1)

steps = [
    (
        "Aktifkan ekstensi pgvector",
        "CREATE EXTENSION IF NOT EXISTS vector;",
    ),
    (
        "Tambah kolom question_embedding vector(384)",
        "ALTER TABLE t_kemhan_feedback "
        "ADD COLUMN IF NOT EXISTS question_embedding vector(384);",
    ),
    (
        "Buat HNSW index untuk cosine similarity",
        """
        CREATE INDEX IF NOT EXISTS idx_feedback_question_embedding
          ON t_kemhan_feedback
          USING hnsw (question_embedding vector_cosine_ops)
          WITH (m = 16, ef_construction = 64);
        """,
    ),
]

for label, sql in steps:
    try:
        print(f"\n[RUN] {label} ...", end=" ")
        cur.execute(sql)
        print("OK")
    except Exception as e:
        print(f"GAGAL\n[ERROR] {e}")
        cur.close()
        conn.close()
        sys.exit(1)

# Verifikasi kolom ada
cur.execute("""
    SELECT column_name, udt_name
    FROM information_schema.columns
    WHERE table_name = 't_kemhan_feedback'
      AND column_name = 'question_embedding';
""")
row = cur.fetchone()
cur.close()
conn.close()

print("\n" + "=" * 60)
if row:
    print(f"[SUKSES] Kolom '{row[0]}' (type: {row[1]}) berhasil ditambahkan.")
    print("Langkah berikutnya:")
    print("  1. Pastikan API sudah di-restart: docker compose up -d --force-recreate api")
    print("  2. Jalankan backfill embedding data lama via:")
    print("     POST /v2/admin/feedback/reembed  (pakai Bearer token admin)")
else:
    print("[WARNING] Kolom tidak ditemukan setelah migration. Cek log di atas.")
print("=" * 60)
