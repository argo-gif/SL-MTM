# Project Specifications: Interactive MTM Service Level KPI & Pareto Analytics Dashboard

## 1. Executive Summary & Core Objectives
Proyek ini bertujuan untuk membangun dashboard analitik interaktif berbasis web untuk memonitor performa Key Performance Indicator (KPI) Service Level MTM (Make-to-Measure / distribusi) PT Konimex. Dashboard ini akan menyajikan data pencapaian pemenuhan pengiriman vs. realisasi, tren bulanan, analisis akar masalah (root cause) dengan visualisasi Tree Maps Pareto multi-dimensi, serta fitur ekspor otomatis ke PowerPoint (PPT) berbasis template `Template PPT.pptx`.

---

## 2. Brand Identity & Visual Theme
- **Primary Palette**: Merah Konimex (Konimex Red), Dark/Light neutral tones, and sleek glassmorphism dashboard layout.
- **Header Component**: Penempatan Logo Resmi Konimex di header dashboard utama dan pada posisi terlindungi pada setiap slide ekspor PPT (sudah disesuaikan dengan `Template PPT.pptx`).
- **Typography & Aesthetics**: Modern UI font (Inter/Outfit), micro-animations, responsive layout.

---

## 3. Architecture & Tech Stack
- **Frontend**:
  - Language: TypeScript
  - Framework/UI: React / Next.js / Vite SPA
  - Styling: Vanilla CSS / Modern CSS Modules (Merah Konimex theme)
  - Visualizations: Interactive Charting Libraries (Chart.js / Recharts / ECharts / D3.js) untuk Pareto Tree Maps & Trend Line Charts.
- **Backend**:
  - Language: Python (Python 3.9+)
  - Framework: FastAPI / Flask RESTful API
  - Data Processing: Pandas, OpenPyXL, NumPy untuk agregasi dan perhitungan logika conditional Service Level & Pareto.
  - PPT Automation: `python-pptx` / Automated slide generation pipeline berbasis `Template PPT.pptx`.
- **Deployment Platform**:
  - Backend: Render.com
  - Frontend: Vercel

---

## 4. Input Data & Storage
- **Input File**: File Excel dataset baku (misalnya `uploaded_active_dataset.xlsx`) yang ditaruh di folder sistem / diproses via upload dashboard.
- **Data Persistence**: Backend local dataset storage & session management.
- **Conditional Logic Filtering (Reason / Alasan)**:
  1. Jika `Alasan Kirim` terisi & `Alasan Realisasi` kosong $\rightarrow$ Menggunakan `Alasan Kirim`.
  2. Jika `Alasan Kirim` kosong & `Alasan Realisasi` terisi $\rightarrow$ Menggunakan `Alasan Realisasi`.
  3. Jika keduanya terisi $\rightarrow$ Menggunakan `Alasan Kirim`.

---

## 5. Functional Requirements & System Modules

### A. Autentikasi & Guarding
- **Login Credentials**:
  - Username: `admin` atau `konimex`
  - Password: `konimex123`
- **Session Guard**: Sesi otomatis berakhir (auto logout) saat browser / tab ditutup.
- **Role Management**:
  - Fitur Upload file Excel hanya dapat diakses oleh user role `admin`.

### B. Filter Global Terintegrasi (Cascading & Searchable & Multi-Select)
- **Delivery Month (Bulan Pengiriman)**: Default memilih bulan transaksi paling akhir.
- **Jenis MTM**: Default terpilih `KA` (Key Account).
- **Dimensi Lain**: Cabang, MTM Alias, Grup Brand, Item / Nama Item.
- **Value Switcher Toggle**:
  - Toggle pilihan tampilan metrik dalam Rupiah (IDR) atau Kuantitas unit (Qty).
  - Default tampilan awal: Rupiah (IDR).

### C. Komponen Visualisasi & Analisis
1. **Scorecard Summary KPI**:
   - Metric cards: Service Level (SL) Kirim %, SL Realisasi %, dan Gap/Selisih (Realisasi - Kirim).
   - Benchmark Line: Fixed Target 85%.
   - Reaktif terhadap kombinasi filter global.
2. **Monthly Performance Trend Line Chart**:
   - Historical run rate hingga bulan yang dipilih.
   - Toggle metrik chart: SL Kirim (default) vs SL Realisasi.
3. **Pareto Tree Maps Multi-Dimensi**:
   - Visualisasi Tree Maps interaktif berbasis kontribusi terbesar ke terkecil (descending Pareto).
   - Dedicated Tabs/Sheets:
     - Sheet Alasan
     - Sheet MTM Alias
     - Sheet Cabang
     - Sheet Grup Brand
     - Sheet Item / Nama Item
   - **Cross-Filtering**: Klik pada blok Tree Maps memfilter seluruh dashboard; klik di area luar membatalkan seleksi.
4. **Data Grid Detail Transaction**:
   - Tabular data grid komprehensif menampilkan rincian transaksi, kalkulasi pemenuhan, dan Pareto.

### D. Automated PowerPoint Export Module
- **Content Checkboxes**: User dapat memilih modul mana yang ingin diekspor.
- **Pareto Sheet Automated Printing**: Mencetak seluruh sheet Tree Maps dan tabel detail pendukung ke slide PPT.
- **Layout Safeguard**: Penempatan visual presisi tinggi agar rasio pas (fit-to-slide) dan **TIDAK MENIMPA** logo Konimex di sudut kanan atas `Template PPT.pptx`.

---

## 6. Definition of Done (Kriteria Selesai Proyek)
- [ ] Backend Python FastAPI & Frontend TypeScript React/Vite berjalan tanpa error secara lokal.
- [ ] Login & Role guard berfungsi (upload hanya admin, auto logout saat tab ditutup).
- [ ] Filter global cascading, switcher IDR/Qty, dan logika alasan berjalan akurat sesuai spesifikasi dataset.
- [ ] Scorecard KPI, Line Chart, Tree Maps Pareto 5 sheet, & Data Grid interaktif dengan cross-filtering.
- [ ] Ekspor PPT otomatis terintegrasi dengan template `Template PPT.pptx` tanpa menimpa logo Konimex.
- [ ] Berhasil di-deploy end-to-end (Backend di Render.com, Frontend di Vercel).
