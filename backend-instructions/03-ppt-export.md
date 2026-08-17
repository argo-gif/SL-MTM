# Backend Instruction 03: Automated PowerPoint (PPT) Export Engine

## 1. Overview
Dokumen ini menjelaskan alur kerja otomasi ekspor laporan analisis Service Level MTM ke format PowerPoint (`.pptx`) berbasis file template `Template PPT.pptx`. 

## 2. Standard Layout Safeguard & Design Rules
- **Template Source**: `Template PPT.pptx` (Dimensi slide: 10.00" x 5.62").
- **Header & Logo Safeguard**:
  - Konimex Logo terletak pada area kanan atas header (`X >= 7.5"`, `Y <= 1.2"`).
  - Seluruh elemen konten visual (kartu KPI, grafik tren, Pareto Tree Maps, dan tabel detail) **TIDAK BOLEH** menimpa area logo Konimex.
- **Content Bounding Box**:
  - `Left`: `0.6"`, `Top`: `1.3"`
  - `Width`: `8.8"`, `Height`: `4.0"`

## 3. Supported Export Modules (Content Selection)
Pengguna dapat memilih modul mana saja yang akan diekspor via checkbox UI:
1. **Slide 1: Executive KPI Summary & Monthly Trend**
   - KPI Scorecard Cards (SL Kirim %, SL Realisasi %, Gap %, Benchmark Target 85%).
   - Summary Monthly Run-rate Performance Table.
2. **Slide 2: Pareto Multi-Dimension Tree Maps (5 Sheets)**
   - Sheet Alasan
   - Sheet MTM Alias
   - Sheet Cabang
   - Sheet Grup Brand
   - Sheet Item / Nama Item
3. **Slide 3: Detail Transaction Grid Table**
   - Summary Rincian Transaksi & Kalkulasi Status Pemenuhan.

## 4. Technical Implementation & XML Generation
- Engine menggunakan pustaka Python `python-pptx` atau manipulasi OpenXML native (`zipfile` & XML) untuk menduplikasi dan menginjeksi slide secara presisi tanpa merusak styling template master.
- Output berupa file buffer/binary file `.pptx` yang siap diunduh pengguna via API `POST /api/export/ppt`.
