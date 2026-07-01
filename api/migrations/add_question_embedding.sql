-- Migration: tambah kolom question_embedding ke t_kemhan_feedback
-- Jalankan SEKALI di database setelah deploy
-- Kolom nullable=True agar backward compatible dengan data lama

-- Pastikan ekstensi pgvector sudah aktif (biasanya sudah dari init dokumen)
CREATE EXTENSION IF NOT EXISTS vector;

-- Tambah kolom embedding 384-dim
ALTER TABLE t_kemhan_feedback
  ADD COLUMN IF NOT EXISTS question_embedding vector(384);

-- Index HNSW untuk cosine similarity search yang cepat (opsional tapi direkomendasikan)
CREATE INDEX IF NOT EXISTS idx_feedback_question_embedding
  ON t_kemhan_feedback
  USING hnsw (question_embedding vector_cosine_ops)
  WITH (m = 16, ef_construction = 64);

-- Verifikasi
SELECT column_name, data_type
FROM information_schema.columns
WHERE table_name = 't_kemhan_feedback'
  AND column_name = 'question_embedding';
