-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create table untuk menyimpan embeddings
-- Karena v_detail_data_terbuka adalah view, kita buat tabel terpisah untuk embeddings
CREATE TABLE IF NOT EXISTS t_data_embeddings (
    id SERIAL PRIMARY KEY,
    kode_data VARCHAR(255) UNIQUE NOT NULL,
    embedding vector(384),  -- 384 dimensions untuk all-MiniLM-L6-v2
    text_content TEXT,  -- Gabungan judul + deskripsi + kategori untuk reference
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Index untuk vector similarity search
CREATE INDEX IF NOT EXISTS idx_data_embeddings_vector 
ON t_data_embeddings USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- Index untuk kode_data lookup
CREATE INDEX IF NOT EXISTS idx_data_embeddings_kode 
ON t_data_embeddings(kode_data);

-- Trigger untuk update timestamp
CREATE OR REPLACE FUNCTION update_embedding_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_embedding_timestamp
BEFORE UPDATE ON t_data_embeddings
FOR EACH ROW
EXECUTE FUNCTION update_embedding_timestamp();
