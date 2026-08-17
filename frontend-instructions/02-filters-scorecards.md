# Frontend Instruction 02: Filter Controls & KPI Scorecards

## 1. Overview
Dokumen ini mendeskripsikan spesifikasi teknis untuk komponen Filter Global Terintegrasi (*Global Linked Cascading Filters*) dan Kartu Metrik Ringkasan KPI (*Scorecard Cards*).

## 2. Integrated Global Linked Filters (Cascading & Searchable)
- **Cascading Filter Behavior**:
  - Saat pilihan filter tingkat atas berubah (misalnya Bulan atau Jenis MTM), pilihan dropdown untuk Cabang, MTM Alias, Grup Brand, dan Item **harus otomatis diperbarui** secara dinamis (cascading) sesuai subset data yang valid.
- **Default Selection Rules**:
  - **Bulan Pengiriman (Delivery Date)**: Default memilih transaksi bulan paling akhir (`latest_month`).
  - **Jenis MTM**: Default memilih `KA` (Key Account).
- **Dimension Filters**:
  - Cabang, MTM Alias, Grup Brand, Item / Nama Item.
- **Metric Switcher Toggle**:
  - `IDR` (Rupiah): Perhitungan berbasis nominal mata uang.
  - `Qty` (Kuantitas): Perhitungan berbasis jumlah unit barang.
  - Default pada awal muat halaman: **Rupiah (IDR)**.

## 3. KPI Scorecards Component Specifications
- **Service Level Kirim Scorecard (%)**:
  - Rumus: `(Total Kirim Sesuai / Total Order) * 100` (IDR / Qty).
- **Service Level Realisasi Scorecard (%)**:
  - Rumus: `(Total Realisasi Sesuai / Total Order) * 100` (IDR / Qty).
- **Gap Realisasi vs Kirim Scorecard (%)**:
  - Rumus: `SL Realisasi (%) - SL Kirim (%)`.
  - Indikator Warna: Hijau (`#4ADE80`) jika positif ($\ge 0$), Merah (`#FF4D4D`) jika negatif ($< 0$).
- **Fixed Benchmark Target**:
  - Garis batas performa target tetap sebesar **85.0%**.
