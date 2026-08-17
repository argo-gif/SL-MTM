# Frontend Instruction 03: Analytics Charts & Pareto Tree Maps (Cross-Filtering)

## 1. Overview
Dokumen ini mendeskripsikan spesifikasi visualisasi grafik tren bulanan (*Monthly Performance Trend Line Chart*) dan visualisasi *Pareto Tree Maps Multi-Dimensi* berbasis fitur *Cross-Filtering*.

## 2. Monthly Performance Trend Component
- **Visualisasi**: Line Chart / Trend Bar yang menampilkan performa historis run-rate bulanan hingga bulan transaksi yang dipilih.
- **Metric Selector Toggle**:
  - `SL Kirim (%)` (Default)
  - `SL Realisasi (%)`
- **Target Line**: Garis acuan target horizontal tetap pada **85.0%**.

## 3. Pareto Tree Maps Multi-Dimensi (5 Dedicated Tabs)
- **Urutan Kontribusi**: Mengurutkan elemen dari kontribusi nilai/kategori terbesar ke terkecil (*descending Pareto*).
- **Dedicated Tabs**:
  1. `Sheet Alasan`
  2. `Sheet MTM Alias`
  3. `Sheet Cabang`
  4. `Sheet Grup Brand`
  5. `Sheet Item / Nama Item`
- **Interaktivitas (Cross-Filtering)**:
  - Klik pada sebuah kotak Tree Map $\rightarrow$ Menerapkan filter global otomatis ke seluruh dashboard berdasarkan elemen tersebut.
  - Efek Visual: Kotak yang dipilih akan mendapatkan penanda border emas (`#FFD700`) dan badge filter aktif.
  - Klik tombol **Reset Filter** atau klik di luar kotak $\rightarrow$ Membatalkan seleksi (*reset cross-filter*).
