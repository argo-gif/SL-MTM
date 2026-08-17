# Frontend Dashboard UI Shell - Dashboard Service Level MTM

Folder ini berisi antarmuka pengguna (UI Shell) berbasis HTML, Merah Konimex Design System CSS, dan TypeScript / ES Modules JavaScript.

---

## Technical Features
1. **Design System & Theme ([src/styles.css](file:///c:/Argo/Project%20AI/SL%20MTM/frontend/src/styles.css))**:
   - Palet visual bernuansa Merah Konimex (`#C00000`, `#8B0000`, `#FFD700` accent).
   - Official Logo Konimex di header dashboard.
   - Glassmorphic scorecards, responsive tree map blocks, dan modal dialog.
2. **Autentikasi & Session Guard ([src/auth.js](file:///c:/Argo/Project%20AI/SL%20MTM/frontend/src/auth.js))**:
   - Modal login kredensial (`admin` / `konimex`, password `konimex123`).
   - Role badge indicator & upload permission check.
   - *Session Guard*: Listener `beforeunload` yang secara otomatis mengosongkan sesi `sessionStorage` (auto logout) saat tab atau window browser ditutup.
3. **Global Linked Filters & Pareto Cross-Filtering ([src/app.js](file:///c:/Argo/Project%20AI/SL%20MTM/frontend/src/app.js))**:
   - Dynamic cascading dropdowns (Bulan, Jenis MTM KA, Cabang, MTM Alias, Grup Brand).
   - Switcher Toggle IDR vs Qty (default IDR).
   - Pareto Tree Maps 5 Dedicated Tabs (Alasan, MTM Alias, Cabang, Grup Brand, Item).
   - **Cross-Filtering**: Klik pada blok Tree Map secara otomatis memfilter seluruh dashboard.
4. **Otomasi Ekspor PowerPoint (PPT)**:
   - Modal checkbox pilihan modul ekspor.
   - Mengunduh file `.pptx` hasil pengolahan backend REST API.

---

## Cara Menjalankan Frontend Secara Lokal

Frontend disajikan langsung oleh server terintegrasi pada port `5000`:

1. Buka browser web (Chrome / Edge / Firefox).
2. Akses alamat lokal:
   ```
   http://127.0.0.1:5000/
   ```
3. Dashboard akan langsung terbuka dengan tema Merah Konimex lengkap dengan Logo Konimex dan data KPI interaktif.
