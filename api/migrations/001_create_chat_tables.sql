-- Chat History Tables
-- Prefix: t_ untuk table

-- Table untuk menyimpan device/user
CREATE TABLE IF NOT EXISTS t_devices (
    id SERIAL PRIMARY KEY,
    device_id VARCHAR(255) UNIQUE NOT NULL,
    device_fingerprint TEXT, -- Browser fingerprint untuk validasi
    user_agent TEXT,
    last_seen_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Table untuk menyimpan session chat
CREATE TABLE IF NOT EXISTS t_chat_sessions (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) UNIQUE NOT NULL,
    device_id VARCHAR(255) NOT NULL,
    title VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (device_id) REFERENCES t_devices(device_id) ON DELETE CASCADE
);

-- Table untuk menyimpan messages
CREATE TABLE IF NOT EXISTS t_chat_messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    role VARCHAR(50) NOT NULL, -- 'user' atau 'assistant'
    content TEXT NOT NULL,
    sources JSONB, -- Untuk menyimpan sumber data (array of objects)
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (session_id) REFERENCES t_chat_sessions(session_id) ON DELETE CASCADE
);

-- Indexes untuk performa
CREATE INDEX IF NOT EXISTS idx_devices_device_id ON t_devices(device_id);
CREATE INDEX IF NOT EXISTS idx_devices_last_seen ON t_devices(last_seen_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_device_id ON t_chat_sessions(device_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_session_id ON t_chat_sessions(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_sessions_updated_at ON t_chat_sessions(updated_at DESC);
CREATE INDEX IF NOT EXISTS idx_chat_messages_session_id ON t_chat_messages(session_id);
CREATE INDEX IF NOT EXISTS idx_chat_messages_created_at ON t_chat_messages(created_at);

-- Function untuk auto-update updated_at
CREATE OR REPLACE FUNCTION update_chat_session_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE t_chat_sessions 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE session_id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger untuk auto-update updated_at saat ada message baru
DROP TRIGGER IF EXISTS trigger_update_chat_session_timestamp ON t_chat_messages;
CREATE TRIGGER trigger_update_chat_session_timestamp
    AFTER INSERT ON t_chat_messages
    FOR EACH ROW
    EXECUTE FUNCTION update_chat_session_timestamp();

-- Function untuk update last_seen_at device
CREATE OR REPLACE FUNCTION update_device_last_seen()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE t_devices 
    SET last_seen_at = CURRENT_TIMESTAMP 
    WHERE device_id = NEW.device_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Trigger untuk auto-update last_seen_at saat ada session baru
DROP TRIGGER IF EXISTS trigger_update_device_last_seen ON t_chat_sessions;
CREATE TRIGGER trigger_update_device_last_seen
    AFTER INSERT ON t_chat_sessions
    FOR EACH ROW
    EXECUTE FUNCTION update_device_last_seen();

