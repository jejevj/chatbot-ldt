-- Migration: tambah kolom document_id ke t_kemhan_faq
-- Jalankan sekali di database production:
--   psql $DATABASE_URL -f migrations/add_document_id_to_faq.sql

ALTER TABLE t_kemhan_faq
  ADD COLUMN IF NOT EXISTS document_id INTEGER
    REFERENCES t_kemhan_documents(id) ON DELETE CASCADE;

CREATE INDEX IF NOT EXISTS idx_kemhan_faq_document_id ON t_kemhan_faq(document_id);

-- Verifikasi
SELECT column_name, data_type, is_nullable
FROM information_schema.columns
WHERE table_name = 't_kemhan_faq'
ORDER BY ordinal_position;
