# Chatbot API - Panduan Penggunaan

Base URL: `http://localhost:8765/chatbot-api`

Swagger UI: `http://localhost:8765/chatbot-api/docs`

---

## Alur Penggunaan

```
1. Register Device → 2. Buat Session → 3. Kirim Pesan → 4. Ulangi Step 3
```

---

## Step 1: Register Device

Setiap client harus register device terlebih dahulu. `device_fingerprint` adalah identifier unik untuk device Anda.

```bash
curl -X POST http://localhost:8765/chatbot-api/device/register \
  -H "Content-Type: application/json" \
  -d '{
    "device_fingerprint": "my-unique-device-id-001"
  }'
```

**Response:**
```json
{
  "device_id": "550e8400-e29b-41d4-a716-446655440000",
  "message": "Device registered successfully"
}
```

> Simpan `device_id` — digunakan sebagai header `X-Device-ID` di semua request berikutnya.

---

## Step 2: Buat Session

```bash
curl -X POST http://localhost:8765/chatbot-api/chat/sessions \
  -H "Content-Type: application/json" \
  -H "X-Device-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{
    "pertanyaan": "Sesi baru"
  }'
```

> Session dibuat otomatis saat pertama kali kirim pesan. Tidak perlu buat session manual.

---

## Step 3: Kirim Pesan (Chat dengan History)

```bash
curl -X POST http://localhost:8765/chatbot-api/chat/history \
  -H "Content-Type: application/json" \
  -H "X-Device-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{
    "pertanyaan": "Apa saja data Open Data yang tersedia?",
    "session_id": null
  }'
```

> Jika `session_id` null, session baru akan dibuat otomatis.

**Response:**
```json
{
  "session_id": "abc123-...",
  "jawaban": "Berikut data Open Data yang tersedia...",
  "sumber": [
    {
      "judul": "Pengguna Jasa Telekomunikasi",
      "url": "https://...",
      "kategori": "Open Data",
      "tipe": "Infografis",
      "kode_data": "KD001"
    }
  ]
}
```

> Simpan `session_id` untuk melanjutkan percakapan di pesan berikutnya.

### Lanjutkan Percakapan

```bash
curl -X POST http://localhost:8765/chatbot-api/chat/history \
  -H "Content-Type: application/json" \
  -H "X-Device-ID: 550e8400-e29b-41d4-a716-446655440000" \
  -d '{
    "pertanyaan": "Berikan detail lebih lanjut",
    "session_id": "abc123-..."
  }'
```

---

## Endpoint Lainnya

### Lihat Semua Session
```bash
curl http://localhost:8765/chatbot-api/chat/sessions \
  -H "X-Device-ID: 550e8400-e29b-41d4-a716-446655440000"
```

### Lihat Pesan dalam Session
```bash
curl http://localhost:8765/chatbot-api/chat/sessions/{session_id} \
  -H "X-Device-ID: 550e8400-e29b-41d4-a716-446655440000"
```

### Hapus Session
```bash
curl -X DELETE http://localhost:8765/chatbot-api/chat/sessions/{session_id} \
  -H "X-Device-ID: 550e8400-e29b-41d4-a716-446655440000"
```

### Update Judul Session
```bash
curl -X PUT "http://localhost:8765/chatbot-api/chat/sessions/{session_id}/title?title=Judul+Baru" \
  -H "X-Device-ID: 550e8400-e29b-41d4-a716-446655440000"
```

### Quick Questions
```bash
curl http://localhost:8765/chatbot-api/chat/quick-questions
```

### Health Check
```bash
curl http://localhost:8765/chatbot-api/health
```

---

## Contoh Script Lengkap

```bash
#!/bin/bash
API_URL="http://localhost:8765/chatbot-api"

# 1. Register device
DEVICE_ID=$(curl -s -X POST $API_URL/device/register \
  -H "Content-Type: application/json" \
  -d '{"device_fingerprint": "my-device-001"}' | jq -r '.device_id')

echo "Device ID: $DEVICE_ID"

# 2. Kirim pesan pertama (session baru)
RESPONSE=$(curl -s -X POST $API_URL/chat/history \
  -H "Content-Type: application/json" \
  -H "X-Device-ID: $DEVICE_ID" \
  -d '{"pertanyaan": "Data apa saja yang tersedia?", "session_id": null}')

SESSION_ID=$(echo $RESPONSE | jq -r '.session_id')
echo "Session ID: $SESSION_ID"
echo "Jawaban: $(echo $RESPONSE | jq -r '.jawaban')"

# 3. Lanjutkan percakapan
curl -s -X POST $API_URL/chat/history \
  -H "Content-Type: application/json" \
  -H "X-Device-ID: $DEVICE_ID" \
  -d "{\"pertanyaan\": \"Berikan contoh data statistik\", \"session_id\": \"$SESSION_ID\"}" | jq '.jawaban'
```
