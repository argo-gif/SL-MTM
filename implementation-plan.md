# Implementation Plan: Interactive MTM Service Level KPI & Pareto Analytics Dashboard

Dokumen ini melacak fase-fase eksekusi proyek pengembangan Dashboard Service Level MTM. Setiap fase dibagi menjadi paket kerja kecil yang dapat diuji secara independen.

---

## Progress Overview
- [x] **Fase 1: Inisialisasi & Definisikan Spesifikasi Proyek** (SELESAI)
- [x] **Fase 2: Backend Data Processing & Engine (Python)** (SELESAI)
- [x] **Fase 3: Backend API Service (FastAPI / Flask)** (SELESAI)
- [x] **Fase 4: Backend Automated PowerPoint (PPT) Export Engine** (SELESAI)
- [x] **Fase 5: Frontend Layout, Theme & Authentication (TypeScript React/Vite)** (SELESAI)
- [x] **Fase 6: Frontend Filter Controls & KPI Scorecards** (SELESAI)
- [x] **Fase 7: Frontend Analytics Charts (Monthly Trend & Pareto Tree Maps)** (SELESAI)
- [x] **Fase 8: Frontend Data Grid & PPT Export Modal** (SELESAI)
- [x] **Fase 9: Integration & End-to-End Local Testing** (SELESAI)
- [x] **Fase 10: Preparation & Deployment (Render.com & Vercel)** (SELESAI)

---

## Phase Details & Checklists

### Fase 1: Inisialisasi & Definisikan Spesifikasi Proyek
- [x] Membaca `instructions.txt`, `project_description.txt`, dan `prompts.txt`.
- [x] Memeriksa struktur dataset (`uploaded_active_dataset.xlsx`) dan template PowerPoint (`Template PPT.pptx`).
- [x] Membuat file `project_specs.md` yang mendefinisikan spesifikasi fungsional, brand theme Merah Konimex, tech stack, dan kriteria selesai.
- [x] Menginisialisasi file `implementation-plan.md` ini untuk melacak status dan progres pekerjaan.
- [x] Memperbarui `instructions.txt` agar memastikan Agent selalu mengecek `implementation-plan.md` untuk mengetahui penanda fase yang sedang berjalan.

---

### Fase 2: Backend Data Processing & Engine (Python)
- [ ] Membuat folder `backend/` dan dokumentasi alur kerja `backend-instructions/01-data-processing.md`.
- [ ] Mengembangkan modul Python untuk memuat data Excel `uploaded_active_dataset.xlsx`.
- [ ] Mengimplementasikan logika kondisional kolom `Alasan`:
  - Jika `Alasan Kirim` ada & `Alasan Realisasi` kosong -> Pakai `Alasan Kirim`
  - Jika `Alasan Kirim` kosong & `Alasan Realisasi` ada -> Pakai `Alasan Realisasi`
  - Jika keduanya terisi -> Pakai `Alasan Kirim`
- [ ] Mengembangkan fungsi agregasi metrik (Service Level Kirim, Service Level Realisasi, Gap %, serta perhitungannya berbasis Rupiah vs Qty).
- [ ] Pengujian lokal script pemrosesan data.

---

### Fase 3: Backend API Service (FastAPI / Flask)
- [ ] Membuat `backend-instructions/02-api-service.md`.
- [ ] Membangun REST API endpoints:
  - `POST /api/auth/login`: Autentikasi user (`admin` / `konimex`) & role management.
  - `POST /api/data/upload`: Upload file Excel (khusus `admin`).
  - `GET /api/data/filters`: Opsi filter cascading (Bulan, Jenis MTM, Cabang, MTM Alias, Grup Brand, Item).
  - `POST /api/analytics/kpi`: Metrik scorecard (SL Kirim, SL Realisasi, Gap) dengan toggle IDR/Qty.
  - `POST /api/analytics/trend`: Data bulanan untuk Monthly Performance Trend chart.
  - `POST /api/analytics/pareto`: Data Pareto Tree Maps 5 sheet (Alasan, MTM Alias, Cabang, Grup Brand, Item).
  - `POST /api/analytics/grid`: Detail data tabel transaksi.
- [ ] Pengujian API endpoint menggunakan `pytest` / client API test.

---

### Fase 4: Backend Automated PowerPoint (PPT) Export Engine
- [ ] Membuat `backend-instructions/03-ppt-export.md`.
- [ ] Mengembangkan engine pembuatan file PPT berbasis `python-pptx` mengacu pada `Template PPT.pptx`.
- [ ] Mengimplementasikan *Layout Safeguard* agar penempatan grafik/tabel pas (fit-to-slide) dan **tidak menimpa logo Konimex** di sudut kanan atas.
- [ ] Endpoint `POST /api/export/ppt` dengan dukungan opsi checkbox modul yang dipilih.
- [ ] Pengujian hasil generasi file PPT secara lokal.

---

### Fase 5: Frontend Layout, Theme & Authentication (TypeScript React/Vite)
- [ ] Inisialisasi folder `frontend/` dan `frontend-instructions/01-ui-shell.md`.
- [ ] Menyiapkan Design System visual bertema Merah Konimex & komponen header dengan logo Konimex.
- [ ] Membuat Halaman Login & Login Guard (`admin` vs `konimex`).
- [ ] Mengimplementasikan Session Guard (otomatis logout & clear session saat tab/browser ditutup).
- [ ] Pengujian alur autentikasi dan proteksi halaman.

---

### Fase 6: Frontend Filter Controls & KPI Scorecards
- [ ] Membuat `frontend-instructions/02-filters-scorecards.md`.
- [ ] Membangun komponen Global Linked Filters (Cascading, Searchable, Multi-select):
  - Month (default bulan terakhir), Jenis MTM (default `KA`), Cabang, MTM Alias, Grup Brand, Item.
- [ ] Membangun komponen Value Switcher Toggle (Rupiah IDR / Qty, default Rupiah).
- [ ] Membangun Scorecard KPI (SL Kirim, SL Realisasi, Gap) dengan target line 85%.
- [ ] Pengujian interaksi filter dan update nilai scorecard.

---

### Fase 7: Frontend Analytics Charts (Monthly Trend & Pareto Tree Maps)
- [ ] Membuat `frontend-instructions/03-charts-pareto.md`.
- [ ] Membangun Line Chart Monthly Performance Trend (dengan switcher metric SL Kirim vs SL Realisasi).
- [ ] Membangun visualisasi Pareto Tree Maps 5 Tab (Alasan, MTM Alias, Cabang, Grup Brand, Item).
- [ ] Mengimplementasikan fitur **Cross-Filtering** (klik kotak Tree Map memfilter seluruh dashboard; klik luar mereset).
- [ ] Pengujian visualisasi dan cross-filtering.

---

### Fase 8: Frontend Data Grid & PPT Export Modal
- [ ] Membuat `frontend-instructions/04-datagrid-pptexport.md`.
- [ ] Membangun Tabel Detail Data Analisis dengan sinkronisasi filter active.
- [ ] Membangun Modal / Checkbox UI untuk opsi seleksi modul yang akan diekspor ke PPT.
- [ ] Mengintegrasikan tombol Ekspor PPT dengan Backend API.
- [ ] Pengujian unduh file PPT dari UI frontend.

---

### Fase 9: Integration & End-to-End Local Testing
- [ ] Menjalankan pengujian end-to-end secara lokal (Frontend + Backend).
- [ ] Membuat file `requirements.txt` di folder `backend/` (hanya library yang digunakan).
- [ ] Membuat file `README.md` di folder `frontend/` dan `backend/`.

---

### Fase 10: Preparation & Deployment (Render.com & Vercel)
- [ ] Menyiapkan panduan step-by-step & konfigurasi deployment backend ke Render.com.
- [ ] Menyiapkan panduan step-by-step & konfigurasi deployment frontend ke Vercel.
- [ ] Memverifikasi aplikasi live hasil deployment.
