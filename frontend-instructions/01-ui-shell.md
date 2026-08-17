# Frontend Instruction 01: Layout Shell, Brand Theme & Authentication

## 1. Overview
Dokumen ini mendeskripsikan spesifikasi antarmuka pengguna (UI Shell), tema visual Merah Konimex, sistem autentikasi pengguna (`admin` / `konimex`), serta penanganan proteksi sesi (*Session Guard*).

## 2. Design System & Brand Identity
- **Primary Color Palette**:
  - Konimex Red: `#C00000` / `#D32F2F`
  - Konimex Red Dark: `#8B0000`
  - Secondary Neutral: `#F8F9FA` / `#1E1E24`
  - Accent Gold: `#FFD700`
- **Header Component**:
  - Penempatan Logo Resmi Konimex di sudut kiri/kanan atas header.
  - Judul Aplikasi: **Interactive MTM Service Level KPI & Pareto Analytics Dashboard**.
  - Badge Peran User (Role badge: Admin vs Konimex User).
  - Tombol Logout Sesi.

## 3. Modul Autentikasi & Session Guard
- **Halaman Login**:
  - Input Username & Password (`admin`/`konimex123` atau `konimex`/`konimex123`).
  - Menyimpan data sesi di `sessionStorage` (Bukan `localStorage`).
- **Session Guard Rule**:
  - Listener `window.addEventListener('beforeunload', ...)` & `visibilitychange` untuk mengosongkan token sesi dan melakukan **auto logout** saat tab atau browser ditutup oleh pengguna.
  - Role Guard: Tombol & Modal Upload Data Excel hanya dirender jika role user adalah `admin`.

## 4. Layout Shell Architecture
- **Header**: Logo Konimex, Title, Role Badge, Logout Button.
- **Top Toolbar**: Global Linked Filters (Cascading & Searchable) & Switcher Toggle IDR vs Qty.
- **Main Dashboard Container**:
  - Section 1: KPI Scorecards (SL Kirim, SL Realisasi, Gap %, Target 85%).
  - Section 2: Line Chart Monthly Performance Trend.
  - Section 3: Pareto Tree Maps Tabs (5 Sheets: Alasan, MTM Alias, Cabang, Grup Brand, Item).
  - Section 4: Detail Transaction Data Grid & PPT Export Modal.
