# Backend Instruction 01: Data Processing Engine

## 1. Overview
Dokumen ini menjelaskan alur kerja pemrosesan data Excel `uploaded_active_dataset.xlsx` untuk menghasilkan agregasi KPI Service Level (SL) MTM dan analisis Pareto multi-dimensi.

## 2. Requirements & Inputs
- **Input File**: File `.xlsx` (default: `uploaded_active_dataset.xlsx`) di root atau folder upload.
- **Library Python**: `pandas`, `openpyxl`, `numpy`.

## 3. Logika Kondisional Alasan (Reasoning Logic)
Sesuai spesifikasi proyek, penentuan nilai kolom `Alasan` terintegrasi mengikuti aturan:
1. Jika `Alasan Kirim` terisi AND `Alasan Realisasi` kosong $\rightarrow$ Menggunakan `Alasan Kirim`.
2. Jika `Alasan Kirim` kosong AND `Alasan Realisasi` terisi $\rightarrow$ Menggunakan `Alasan Realisasi`.
3. Jika keduanya terisi $\rightarrow$ Menggunakan `Alasan Kirim`.
4. Jika keduanya kosong $\rightarrow$ Set sebagai `'Tanpa Alasan'` atau `'Kirim Sesuai / On-Time'`.

## 4. Agregasi Metrik & Calculation Rules
- **Service Level Kirim (%)**: `(Total Kirim Sesuai / Total Order) * 100` (atau berbasis Rupiah / Qty).
- **Service Level Realisasi (%)**: `(Total Realisasi Sesuai / Total Order) * 100` (atau berbasis Rupiah / Qty).
- **Gap Realisasi vs Kirim**: `SL Realisasi (%) - SL Kirim (%)`.
- **Target Benchmark**: Garis acuan fixed 85%.
- **Value Switcher Toggle**:
  - `IDR` (Rupiah): Menggunakan perkalian kuantitas dan harga satuan / nilai nominal transaksi.
  - `Qty` (Kuantitas): Menggunakan total jumlah unit/koli barang.
- **Cascading Global Filters**:
  - Month (Bulan Pengiriman)
  - Jenis MTM (Default: `KA`)
  - Cabang
  - MTM Alias
  - Grup Brand
  - Item / Nama Item

## 5. Output Data Structures for Visualizations
- **KPI Summary Scorecard**: JSON object berisi `{ sl_kirim, sl_realisasi, gap, target: 85 }`.
- **Monthly Trend Chart**: Array of monthly objects berisi `{ month, sl_kirim, sl_realisasi }`.
- **Pareto Tree Maps (5 Sheets)**:
  1. `Alasan`
  2. `MTM Alias`
  3. `Cabang`
  4. `Grup Brand`
  5. `Item / Nama Item`
  Setiap sheet berisi array data terurut descending berdasarkan kontribusi Pareto (nilai/qty keterlambatan/gap) beserta akumulasi persentase Pareto.
- **Detail Transaction Grid**: Rows data transaksi terfilter dengan kalkulasi status pemenuhan dan alasan akhir.
