# Error Handling & Maintenance Mode

Dokumentasi untuk error handling dan maintenance mode pada aplikasi Chatbot Satu Data Pertahanan.

## Frontend Error Handling

### Error Pages

Aplikasi memiliki halaman error yang menangani berbagai kondisi:

1. **404 - Halaman Tidak Ditemukan**
   - Ditampilkan ketika user mengakses URL yang tidak terdaftar
   - Menyediakan tombol untuk kembali ke beranda atau halaman sebelumnya

2. **500 - Server Error**
   - Ditampilkan ketika terjadi kesalahan pada server
   - Menampilkan pesan error yang user-friendly

3. **Maintenance Mode**
   - Ditampilkan ketika sistem sedang dalam pemeliharaan
   - Menampilkan estimasi waktu selesai (jika tersedia)
   - Menyediakan tombol untuk cek status sistem

4. **Network Error**
   - Ditampilkan ketika tidak dapat terhubung ke server
   - Memberikan saran untuk memeriksa koneksi internet

### Routing

Aplikasi menggunakan Vue Router untuk menangani navigasi:

```javascript
// Akses error page secara manual
router.push({
  name: 'Error',
  params: { type: '404' } // atau '500', 'maintenance', 'network'
})
```

### API Error Interceptor

Semua error dari API akan ditangani secara otomatis oleh axios interceptor:

```javascript
// Error types yang ditangani:
- validation (400)
- unauthorized (401)
- forbidden (403)
- notfound (404)
- ratelimit (429)
- server (500)
- maintenance (503)
- network (no response)
```

Error object yang dikembalikan:
```javascript
{
  type: 'server',
  message: 'Terjadi kesalahan pada server',
  statusCode: 500,
  data: {...}
}
```

## Maintenance Mode

### Frontend Configuration

Edit file `.env` atau `.env.local`:

```env
# Aktifkan maintenance mode
VITE_MAINTENANCE_MODE=true

# Custom message (opsional)
VITE_MAINTENANCE_MESSAGE=Sistem sedang dalam pemeliharaan

# Estimasi waktu selesai (opsional)
VITE_MAINTENANCE_ETA=2 jam
```

Atau edit `frontend/src/config/index.js`:

```javascript
maintenance: {
  enabled: true,
  message: 'Sistem sedang dalam pemeliharaan',
  eta: '23:00 WIB'
}
```

### Backend Configuration

Edit file `api/.env`:

```env
# Aktifkan maintenance mode
MAINTENANCE_MODE=true

# Custom message (opsional)
MAINTENANCE_MESSAGE=Sistem sedang dalam pemeliharaan untuk meningkatkan kualitas layanan

# Estimasi waktu selesai (opsional)
MAINTENANCE_ETA=2 jam
```

Atau edit `api/app/config.py`:

```python
MAINTENANCE_MODE: bool = True
MAINTENANCE_MESSAGE: str = "Sistem sedang dalam pemeliharaan"
MAINTENANCE_ETA: Optional[str] = "23:00 WIB"
```

### Behavior saat Maintenance Mode

**Frontend:**
- Semua route akan redirect ke halaman maintenance
- Kecuali route `/error/*` untuk menampilkan halaman error

**Backend:**
- Semua endpoint akan return HTTP 503
- Kecuali endpoint: `/health`, `/`, `/docs`, `/redoc`, `/openapi.json`
- Response body:
  ```json
  {
    "detail": "Sistem sedang dalam pemeliharaan",
    "eta": "2 jam",
    "status": "maintenance"
  }
  ```

## Testing Error Pages

### Test 404 Page
```
http://localhost:3210/chatbot/halaman-tidak-ada
```

### Test Maintenance Mode

1. Set `VITE_MAINTENANCE_MODE=true` di frontend `.env`
2. Restart dev server
3. Akses aplikasi

### Test API Maintenance Mode

1. Set `MAINTENANCE_MODE=true` di backend `.env`
2. Restart API server
3. Coba akses endpoint (akan return 503)

### Test Network Error

1. Matikan backend API
2. Coba kirim chat message
3. Error network akan tertangkap dan ditampilkan

## URL Structure

### Frontend
- Base URL: `http://localhost:3210/chatbot/`
- Error pages: `http://localhost:3210/chatbot/error/404`

### Backend
- Base URL: `http://localhost:8080/chatbot-api/`
- Health check: `http://localhost:8080/chatbot-api/health`
- API docs: `http://localhost:8080/chatbot-api/docs`

## Production Deployment

### Nginx Configuration Example

```nginx
# Frontend
location /chatbot/ {
    alias /var/www/chatbot/dist/;
    try_files $uri $uri/ /chatbot/index.html;
}

# Backend API
location /chatbot-api/ {
    proxy_pass http://localhost:8080/chatbot-api/;
    proxy_set_header Host $host;
    proxy_set_header X-Real-IP $remote_addr;
}
```

### Environment Variables

**Production Frontend (.env.production):**
```env
VITE_API_BASE_URL=https://yourdomain.com/chatbot-api
VITE_MAINTENANCE_MODE=false
VITE_SHOW_ERROR_DETAILS=false
```

**Production Backend (.env):**
```env
MAINTENANCE_MODE=false
LOG_LEVEL=WARNING
API_RELOAD=false
```

## Troubleshooting

### Error: "Cannot read property 'enhanced' of undefined"
- Pastikan semua API calls menggunakan try-catch
- Error interceptor akan menambahkan property `enhanced` ke error object

### Maintenance page tidak muncul
- Cek environment variable sudah benar
- Restart dev server setelah mengubah .env
- Cek browser console untuk error

### API masih bisa diakses saat maintenance
- Pastikan `MAINTENANCE_MODE=true` di backend .env
- Restart API server
- Cek endpoint yang dikecualikan di middleware

### 404 page tidak muncul untuk route tidak valid
- Pastikan vue-router sudah terinstall
- Cek router configuration di `frontend/src/router/index.js`
- Pastikan catch-all route `/:pathMatch(.*)*` ada di akhir routes array
