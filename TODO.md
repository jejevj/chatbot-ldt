# TODO — Backoffice Frontend
> Dibuat: 2026-07-02 03:36 WIB
> Update: 2026-07-02 03:49 WIB

---

## Status Selesai ✅

- [x] Setup Vue Router dengan base `/chatbot/`
- [x] Route `/backoffice/login` — form login admin
- [x] Route `/backoffice/ai-management` — halaman dengan 3 tab
- [x] Auth store (`stores/auth.js`) — simpan JWT di localStorage
- [x] Auth service (`services/authService.js`) — POST `/v2/admin/login`
- [x] Navigation guard — protected route & guest-only redirect
- [x] `BackofficeLayout.vue` — sidebar + topbar, glassmorphism theme
- [x] `backofficeApi.js` — wrapper fetch Bearer token + auto logout jika 401
- [x] `ConfirmModal.vue` — modal konfirmasi hapus
- [x] `StatusBadge.vue` — badge warna per status
- [x] `DocumentsTab.vue` — upload, list, hapus dokumen RAG
- [x] `FAQTab.vue` — CRUD FAQ
- [x] `FeedbackTab.vue` — koreksi AI, apply ground truth
- [x] Glassmorphism theme base colour `#5e3f1f`
- [x] `LoginPage.vue` redesign glassmorphism
- [x] Lucide icons (ganti emoji)

---

## Todo 🔲

### Polish & UX
- [ ] Toast notifikasi global sukses/gagal (saat ini hanya inline message)
- [ ] Auto-refresh status dokumen `processing` setiap 5 detik sampai `ready`
- [ ] Pagination tabel jika data banyak
- [ ] Search/filter di tabel Dokumen & FAQ
- [ ] Responsive layout untuk mobile/tablet
- [ ] Skeleton loading state (saat ini hanya spinner)

### Halaman Tambahan (Opsional)
- [ ] Dashboard summary — total dokumen, FAQ, feedback pending
- [ ] Halaman manajemen user admin
