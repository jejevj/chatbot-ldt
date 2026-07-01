-- =============================================================
-- Migration 004: V2 Kemhan Chatbot Tables
-- Tabel-tabel untuk fitur RAG chatbot Kemhan (v2)
-- Jalankan setelah 001, 002, 003
-- =============================================================

-- Pastikan pgvector sudah aktif (sudah di 002, tapi aman diulang)
CREATE EXTENSION IF NOT EXISTS vector;


-- -------------------------------------------------------------
-- 1. Dokumen rujukan yang diupload admin
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS t_kemhan_documents (
    id           SERIAL PRIMARY KEY,
    judul        VARCHAR(500)  NOT NULL,
    filename     VARCHAR(500)  NOT NULL,
    filepath     TEXT          NOT NULL,
    tipe         VARCHAR(50)   NOT NULL DEFAULT 'umum', -- regulasi, uu, faq, umum
    status       VARCHAR(20)   NOT NULL DEFAULT 'processing', -- processing, ready, error
    error_message TEXT,
    total_chunks INTEGER       NOT NULL DEFAULT 0,
    uploaded_at  TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at   TIMESTAMP     NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_kemhan_docs_status     ON t_kemhan_documents(status);
CREATE INDEX IF NOT EXISTS idx_kemhan_docs_tipe       ON t_kemhan_documents(tipe);
CREATE INDEX IF NOT EXISTS idx_kemhan_docs_uploaded   ON t_kemhan_documents(uploaded_at DESC);


-- -------------------------------------------------------------
-- 2. Potongan teks (chunks) dari setiap dokumen
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS t_kemhan_doc_chunks (
    id          SERIAL PRIMARY KEY,
    doc_id      INTEGER NOT NULL REFERENCES t_kemhan_documents(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    chunk_text  TEXT    NOT NULL,
    token_count INTEGER NOT NULL DEFAULT 0,
    created_at  TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_kemhan_chunks_doc_id ON t_kemhan_doc_chunks(doc_id);


-- -------------------------------------------------------------
-- 3. Vector embedding per chunk
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS t_kemhan_embeddings (
    id         SERIAL PRIMARY KEY,
    chunk_id   INTEGER NOT NULL UNIQUE REFERENCES t_kemhan_doc_chunks(id) ON DELETE CASCADE,
    embedding  vector(384), -- 384 dimensions (all-MiniLM-L6-v2)
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_kemhan_embeddings_chunk ON t_kemhan_embeddings(chunk_id);
-- Index untuk vector similarity search (cosine)
CREATE INDEX IF NOT EXISTS idx_kemhan_embeddings_vector
    ON t_kemhan_embeddings USING ivfflat (embedding vector_cosine_ops)
    WITH (lists = 100);


-- -------------------------------------------------------------
-- 4. FAQ yang dikelola admin
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS t_kemhan_faq (
    id          SERIAL PRIMARY KEY,
    pertanyaan  TEXT         NOT NULL,
    jawaban     TEXT         NOT NULL,
    kategori    VARCHAR(100) NOT NULL DEFAULT 'umum',
    is_active   BOOLEAN      NOT NULL DEFAULT TRUE,
    created_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at  TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_kemhan_faq_is_active ON t_kemhan_faq(is_active);
CREATE INDEX IF NOT EXISTS idx_kemhan_faq_kategori  ON t_kemhan_faq(kategori);


-- -------------------------------------------------------------
-- 5. Koreksi jawaban AI oleh admin (ground truth training)
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS t_kemhan_feedback (
    id                SERIAL PRIMARY KEY,
    pertanyaan_asli   TEXT      NOT NULL,
    jawaban_ai        TEXT      NOT NULL,
    jawaban_koreksi   TEXT      NOT NULL,
    catatan_admin     TEXT,
    status            VARCHAR(20) NOT NULL DEFAULT 'pending', -- pending, applied
    applied_at        TIMESTAMP,
    created_at        TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_kemhan_feedback_status ON t_kemhan_feedback(status);


-- -------------------------------------------------------------
-- 6. Sesi percakapan chatbot Kemhan
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS t_kemhan_chat_sessions (
    id         SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL UNIQUE,
    device_id  VARCHAR(255),
    title      VARCHAR(500),
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_kemhan_sessions_session_id ON t_kemhan_chat_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_kemhan_sessions_device_id  ON t_kemhan_chat_sessions(device_id);
CREATE INDEX IF NOT EXISTS idx_kemhan_sessions_updated    ON t_kemhan_chat_sessions(updated_at DESC);


-- -------------------------------------------------------------
-- 7. Pesan dalam sesi percakapan
-- -------------------------------------------------------------
CREATE TABLE IF NOT EXISTS t_kemhan_chat_messages (
    id         SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL REFERENCES t_kemhan_chat_sessions(session_id) ON DELETE CASCADE,
    role       VARCHAR(20)  NOT NULL, -- user, assistant
    content    TEXT         NOT NULL,
    sources    JSONB,
    created_at TIMESTAMP    NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_kemhan_messages_session_id ON t_kemhan_chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_kemhan_messages_created    ON t_kemhan_chat_messages(created_at);


-- -------------------------------------------------------------
-- Triggers: auto-update updated_at
-- -------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_kemhan_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Dokumen
DROP TRIGGER IF EXISTS trg_kemhan_docs_updated ON t_kemhan_documents;
CREATE TRIGGER trg_kemhan_docs_updated
    BEFORE UPDATE ON t_kemhan_documents
    FOR EACH ROW EXECUTE FUNCTION update_kemhan_timestamp();

-- FAQ
DROP TRIGGER IF EXISTS trg_kemhan_faq_updated ON t_kemhan_faq;
CREATE TRIGGER trg_kemhan_faq_updated
    BEFORE UPDATE ON t_kemhan_faq
    FOR EACH ROW EXECUTE FUNCTION update_kemhan_timestamp();

-- Chat sessions
DROP TRIGGER IF EXISTS trg_kemhan_sessions_updated ON t_kemhan_chat_sessions;
CREATE TRIGGER trg_kemhan_sessions_updated
    BEFORE UPDATE ON t_kemhan_chat_sessions
    FOR EACH ROW EXECUTE FUNCTION update_kemhan_timestamp();

-- Auto-update session updated_at saat ada pesan baru
CREATE OR REPLACE FUNCTION update_kemhan_session_on_message()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE t_kemhan_chat_sessions
    SET updated_at = CURRENT_TIMESTAMP
    WHERE session_id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_kemhan_session_on_msg ON t_kemhan_chat_messages;
CREATE TRIGGER trg_kemhan_session_on_msg
    AFTER INSERT ON t_kemhan_chat_messages
    FOR EACH ROW EXECUTE FUNCTION update_kemhan_session_on_message();
