# Backend Engine & REST API Service - Dashboard Service Level MTM

Folder ini berisi kode backend Python untuk pengolahan data Excel, penyediaan layanan REST API, serta engine ekspor otomatis PowerPoint (`.pptx`).

---

## Technical Features
1. **Data Processing Engine ([data_processor.py](file:///c:/Argo/Project%20AI/SL%20MTM/backend/data_processor.py))**:
   - Memuat dataset Excel [uploaded_active_dataset.xlsx](file:///c:/Argo/Project%20AI/SL%20MTM/uploaded_active_dataset.xlsx).
   - Logika kondisional alasan: Alasan Kirim vs Alasan Realisasi.
   - Agregasi KPI Scorecard (SL Kirim %, SL Realisasi %, Gap %, target benchmark fixed 85%).
   - Pareto Tree Maps 5 Dimensi (`alasan`, `mtm_alias`, `cabang`, `grup_brand`, `item`).
2. **REST API Service ([app_standalone.py](file:///c:/Argo/Project%20AI/SL%20MTM/backend/app_standalone.py))**:
   - `POST /api/auth/login`: Autentikasi user (`admin` / `konimex`).
   - `POST /api/data/upload`: Upload file dataset (khusus role `admin`).
   - `GET /api/data/filters`: Pilihan filter global cascading.
   - `POST /api/analytics/kpi`: Metrik scorecard KPI.
   - `POST /api/analytics/trend`: Performa tren bulanan.
   - `POST /api/analytics/pareto`: Data Pareto Tree Maps 5 sheet.
   - `POST /api/analytics/grid`: Rincian transaksi data grid.
   - `POST /api/export/ppt`: Generasi dan pengunduhan file `.pptx`.
3. **PowerPoint Export Engine ([ppt_exporter.py](file:///c:/Argo/Project%20AI/SL%20MTM/backend/ppt_exporter.py))**:
   - Injeksi visual & tabel ke [Template PPT.pptx](file:///c:/Argo/Project%20AI/SL%20MTM/Template%20PPT.pptx).
   - *Layout Safeguard*: Memastikan posisi visual pas (bounding box X: 0.6", Y: 1.3", W: 8.8") dan **tidak menimpa logo Konimex** di kanan atas.

---

## Cara Menjalankan Backend Secara Lokal

### Langkah 1: Masuk ke folder backend / root
```bash
cd "c:\Argo\Project AI\SL MTM"
```

### Langkah 2: Menjalankan Server Backend Python
```bash
# Menggunakan virtual environment yang sudah dikonfigurasi:
& "backend/venv/bin/python" backend/app_standalone.py
```

Server backend REST API akan aktif di `http://127.0.0.1:5000`.
