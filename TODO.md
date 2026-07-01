# TODO — Backoffice Frontend
> Dibuat: 2026-07-02 03:36 WIB

---

## Status Selesai ✅

- [x] Setup Vue Router dengan base `/chatbot/`
- [x] Route `/backoffice/login` — form login admin
- [x] Route `/backoffice/ai-management` — blank page
- [x] Auth store (`stores/auth.js`) — simpan JWT di localStorage
- [x] Auth service (`services/authService.js`) — POST `/v2/admin/login`
- [x] Navigation guard — protected route & guest-only redirect
- [x] `BackofficeLayout.vue` — sidebar + topbar

---

## Todo 🔲

### 1. API Service Layer
- [ ] Buat `services/backofficeApi.js` — wrapper fetch dengan header `Authorization: Bearer <token>` untuk semua endpoint admin
- [ ] Handle token expired / 401 → auto logout + redirect ke login

---

### 2. Halaman `/backoffice/ai-management` — 3 Tab

#### Tab 1: 📄 Dokumen RAG
| Fitur | Method | Endpoint |
|---|---|---|
| List semua dokumen | `GET` | `/v2/admin/documents` |
| Upload dokumen baru | `POST` | `/v2/admin/documents` (multipart: `judul`, `tipe`, `file`) |
| Hapus dokumen | `DELETE` | `/v2/admin/documents/{doc_id}` |

- [ ] Tabel list dokumen (judul, tipe, status, tanggal upload)
- [ ] Badge status: `processing` (kuning) / `ready` (hijau) / `error` (merah)
- [ ] Form upload: input judul, select tipe, file picker (PDF/DOCX/TXT)
- [ ] Tombol hapus dengan modal konfirmasi

#### Tab 2: ❓ FAQ
| Fitur | Method | Endpoint |
|---|---|---|
| List semua FAQ | `GET` | `/v2/admin/faq` |
| Tambah FAQ | `POST` | `/v2/admin/faq` |
| Edit FAQ | `PUT` | `/v2/admin/faq/{faq_id}` |
| Hapus FAQ | `DELETE` | `/v2/admin/faq/{faq_id}` |

- [ ] Tabel list FAQ (pertanyaan, jawaban, status aktif)
- [ ] Form tambah FAQ (pertanyaan, jawaban)
- [ ] Inline edit atau modal edit FAQ
- [ ] Tombol hapus dengan modal konfirmasi
- [ ] Toggle aktif/nonaktif

#### Tab 3: 🔁 Feedback / Koreksi AI
| Fitur | Method | Endpoint |
|---|---|---|
| List semua feedback | `GET` | `/v2/admin/feedback` |
| Tambah koreksi manual | `POST` | `/v2/admin/feedback` |
| Apply sebagai ground truth | `POST` | `/v2/admin/feedback/{id}/apply` |
| Hapus feedback | `DELETE` | `/v2/admin/feedback/{id}` |

- [ ] Tabel list feedback (pertanyaan asal, jawaban AI, koreksi admin, status)
- [ ] Badge status: `pending` (abu) / `applied` (hijau)
- [ ] Tombol "Apply" untuk jadikan ground truth
- [ ] Form tambah koreksi manual
- [ ] Tombol hapus dengan modal konfirmasi

---

### 3. Komponen Shared (Reusable)
- [ ] `components/backoffice/ConfirmModal.vue` — modal konfirmasi hapus
- [ ] `components/backoffice/StatusBadge.vue` — badge warna berdasarkan status
- [ ] `components/backoffice/DataTable.vue` — tabel dengan loading skeleton & empty state
- [ ] `components/backoffice/TabNav.vue` — navigasi tab

---

### 4. Route Sidebar (Opsional — jika dipisah halaman)
```
/backoffice/ai-management   ← sudah ada (akan diisi 3 tab)
/backoffice/documents       ← opsional
/backoffice/faq             ← opsional
/backoffice/feedback        ← opsional
```

---

### 5. Polish & UX
- [ ] Loading state saat fetch data (skeleton atau spinner)
- [ ] Toast notifikasi sukses/gagal setelah aksi (upload, hapus, apply)
- [ ] Empty state jika data kosong
- [ ] Responsive layout (minimal tablet)
