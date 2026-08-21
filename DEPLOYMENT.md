# Panduan Deployment End-to-End: Dashboard Service Level MTM

Dokumen ini berisi panduan lengkap langkah demi langkah (*step-by-step*) untuk melakukan deployment **Dashboard Service Level MTM (PT Konimex)** ke cloud platform (**Render.com** untuk Backend REST API dan **Vercel** untuk Frontend UI), serta opsi deployment server mandiri / Docker.

---

## 🏗️ Struktur Arsitektur Deployment

```
                   +-----------------------------------+
                   |         Pengguna Browser          |
                   +-----------------------------------+
                                     |
                                     v
                   +-----------------------------------+
                   |     Frontend (Vercel / Static)    |
                   |   - HTML5 / CSS3 / ES Modules     |
                   +-----------------------------------+
                                     |
                               (REST API Calls)
                                     v
                   +-----------------------------------+
                   |     Backend (Render.com / WSGI)   |
                   |   - Python Flask / Gunicorn       |
                   |   - SQLite dataset.db Engine      |
                   |   - Automated PPT Generator       |
                   +-----------------------------------+
```

---

## 🚀 Opsi 1: Deployment Dual-Platform (Render.com + Vercel)

### 1. Deployment Backend ke Render.com

1. **Persiapan Repository Git**:
   Pastikan seluruh proyek (termasuk folder `backend/` dan `render.yaml`) telah di-commit dan di-push ke repository GitHub / GitLab Anda:
   ```bash
   git add .
   git commit -m "Feat: Complete SL MTM Dashboard backend ready for deployment"
   git push origin main
   ```

2. **Buat Web Service Baru di Render**:
   - Buka [Render Dashboard](https://dashboard.render.com/) dan pilih **New +** -> **Web Service**.
   - Hubungkan repository Git Anda.
   - Pilih opsi **Blueprint** (Render akan otomatis mendeteksi file [`render.yaml`](file:///c:/Argo/Project%20AI/SL%20MTM/render.yaml)) **atau** buat secara manual dengan parameter berikut:
     * **Name**: `sl-mtm-backend`
     * **Environment**: `Python 3`
     * **Build Command**: `pip install -r backend/requirements.txt`
     * **Start Command**: `gunicorn --bind 0.0.0.0:$PORT backend.app:app`
     * **Python Version**: `3.10.0`

3. **Verifikasi Deployment Backend**:
   Setelah build selesai di Render, uji endpoint kesehatan server:
   ```
   https://sl-mtm-backend.onrender.com/api/health
   ```
   *Respon Berhasil:* `{"service": "SL MTM Analytics Backend (Flask/Gunicorn)", "status": "ok"}`

---

### 2. Deployment Frontend ke Vercel

1. **Hubungkan Repository ke Vercel**:
   - Buka [Vercel Dashboard](https://vercel.com/dashboard) dan klik **Add New...** -> **Project**.
   - Impor repository Git proyek ini.

2. **Konfigurasi Project Vercel**:
   - **Framework Preset**: `Other`
   - **Root Directory**: `./` (atau pilih folder `frontend`)
   - Vercel akan membaca konfigurasi dari [`vercel.json`](file:///c:/Argo/Project%20AI/SL%20MTM/vercel.json) secara otomatis.

3. **Hubungkan API URL Backend**:
   - Pada file `frontend/src/app.js`, sesuaikan `apiBaseUrl` dengan URL Render backend Anda:
     ```javascript
     this.apiBaseUrl = 'https://sl-mtm-backend.onrender.com';
     ```
   - Lakukan commit dan push ke Git. Vercel akan otomatis melakukan *Auto-Deploy*.

---

## 🖥️ Opsi 2: Deployment Single-Server (VPS / Server Lokal)

Jika aplikasi ingin dijalankan pada 1 server fisik/VPS internal perusahaan PT Konimex:

1. **Menjalankan Service Standalone (Python Native)**:
   ```bash
   cd "c:\Argo\Project AI\SL MTM"
   python backend/app_standalone.py
   ```
   Aplikasi dan frontend siap diakses pada `http://<IP_SERVER>:5000/`.

2. **Menjalankan Service dengan Gunicorn (Linux VPS)**:
   ```bash
   cd /path/to/SL-MTM
   pip install -r backend/requirements.txt
   gunicorn --bind 0.0.0.0:5000 --workers 4 backend.app:app
   ```

---

## 🔒 Konfigurasi Keamanan & Kredensial Production

| Komponen | Parameter | Nilai Default |
| :--- | :--- | :--- |
| **Port Server** | `PORT` | `5000` |
| **Admin Login** | Username / Password | `admin` / `konimex123` |
| **User Login** | Username / Password | `konimex` / `konimex123` |
| **Upload Guard** | Password Otorisasi Upload | `Adelle@0403` |

---

## 🛠️ Ringkasan Berkas Deployment Konfigurasi

- [`render.yaml`](file:///c:/Argo/Project%20AI/SL%20MTM/render.yaml) — Konfigurasi Render.com Web Service
- [`vercel.json`](file:///c:/Argo/Project%20AI/SL%20MTM/vercel.json) — Konfigurasi Routing & Static Host Vercel
- [`backend/requirements.txt`](file:///c:/Argo/Project%20AI/SL%20MTM/backend/requirements.txt) — Dependensi Python Backend
- [`backend/app.py`](file:///c:/Argo/Project%20AI/SL%20MTM/backend/app.py) — WSGI Application Entrypoint (Flask)
- [`backend/app_standalone.py`](file:///c:/Argo/Project%20AI/SL%20MTM/backend/app_standalone.py) — Embedded Standalone Web Server
