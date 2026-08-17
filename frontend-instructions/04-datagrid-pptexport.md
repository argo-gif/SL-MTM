# Frontend Instruction 04: Detail Data Grid & PPT Export Modal

## 1. Overview
Dokumen ini mendeskripsikan spesifikasi teknis untuk komponen Tabel Detail Data Analisis Transaksi (*Detail Data Grid Table*) dan Modal UI Otomasi Ekspor PowerPoint (*PPT Export Selection Modal*).

## 2. Detail Data Grid Table Specifications
- **Sinkronisasi Filter**: Menampilkan baris transaksi yang telah disaring secara presisi sesuai kombinasi *Global Linked Filters* dan *Cross-Filtering* Tree Map yang sedang aktif.
- **Kolom Utama Tabel Grid**:
  1. Bulan (`month`)
  2. Jenis MTM (`mtm_type`)
  3. Cabang (`branch`)
  4. MTM Alias (`mtm_alias`)
  5. Grup Brand (`brand_group`)
  6. Nama Item (`item_name`)
  7. R_Kirim IDR (`idr_kirim`)
  8. RP_Realisasi IDR (`idr_realisasi`)
  9. Alasan Akhir (`reason_final`) – Diberi penanda warna hijau jika `'On-Time / Sesuai'` dan kuning/merah jika terdapat alasan keterlambatan.
- **Counter Badge**: Menampilkan jumlah total baris transaksi terfilter (contoh: *"50 Transaksi Terfilter"*).

## 3. Automated PowerPoint (PPT) Export Modal Specifications
- **Trigger**: Tombol **"Ekspor PowerPoint"** pada baris kontrol filter utama.
- **Opsi Seleksi Modul (Checkboxes)**:
  - `[x]` Executive KPI & Monthly Trend
  - `[x]` Pareto Tree Maps (5 Sheets)
  - `[x]` Detail Data Grid Table
- **Interaksi & Unduh File**:
  - Mengirim payload filter aktif dan pilihan checkbox ke endpoint `POST /api/export/ppt`.
  - Mengubah tombol menjadi state loading (*"Mengekspor Slide PPT..."*).
  - Mengunduh file binary `.pptx` hasil otomasi ekspor secara otomatis di browser pengguna.
  - Memastikan *Layout Safeguard* terpenuhi (rasio fit-to-slide dan tidak menimpa logo Konimex di sudut kanan atas).
