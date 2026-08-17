# Backend Instruction 02: API Service (Flask / RESTful API)

## 1. Overview
Dokumen ini mendeskripsikan spesifikasi endpoint REST API untuk melayani kebutuhan frontend Dashboard Service Level MTM, mencakup autentikasi user, pengelolaan filter global cascading, metrik KPI, tren bulanan, Pareto Tree Maps 5 dimensi, serta detail tabel transaksi.

## 2. API Endpoints Specification

### A. Authentication & User Access
- **Endpoint**: `POST /api/auth/login`
- **Request Body**:
  ```json
  {
    "username": "admin",
    "password": "konimex123"
  }
  ```
- **Credentials Validation**:
  - Valid Users: `admin` / `konimex`
  - Valid Password: `konimex123`
- **Response**:
  ```json
  {
    "status": "success",
    "user": {
      "username": "admin",
      "role": "admin",
      "can_upload": true
    },
    "token": "session_token_12345"
  }
  ```

### B. File Upload (Admin Only)
- **Endpoint**: `POST /api/data/upload`
- **Headers**: Multipart Form-Data (file field: `file`)
- **Role Guard**: Mengembalikan status `403 Forbidden` jika role bukan `admin`.
- **Response**:
  ```json
  {
    "status": "success",
    "message": "Dataset Excel berhasil diunggah dan diperbarui."
  }
  ```

### C. Global Cascading Filters
- **Endpoint**: `GET /api/data/filters`
- **Response**:
  ```json
  {
    "months": ["2025-10", "2025-11", "2025-12"],
    "latest_month": "2025-12",
    "mtm_types": ["KA", "REGULAR"],
    "default_mtm_type": "KA",
    "branches": ["Cabang A", "Cabang B"],
    "mtm_aliases": ["Alias 1", "Alias 2"],
    "brand_groups": ["Group 1", "Group 2"],
    "items": ["Item A", "Item B"]
  }
  ```

### D. Analytics - KPI Scorecard
- **Endpoint**: `POST /api/analytics/kpi`
- **Request Body**:
  ```json
  {
    "month": "2025-12",
    "mtm_type": "KA",
    "metric_type": "idr", // "idr" atau "qty"
    "branches": [],
    "mtm_aliases": [],
    "brand_groups": [],
    "items": []
  }
  ```
- **Response**:
  ```json
  {
    "sl_kirim": 88.5,
    "sl_realisasi": 84.2,
    "gap": -4.3,
    "target": 85.0
  }
  ```

### E. Analytics - Monthly Trend
- **Endpoint**: `POST /api/analytics/trend`
- **Request Body**: Filter global tanpa pembatasan bulan tunggal.
- **Response**: Array of monthly performance objects.

### F. Analytics - Pareto Tree Maps (5 Sheets)
- **Endpoint**: `POST /api/analytics/pareto`
- **Request Body**:
  ```json
  {
    "dimension": "alasan", // "alasan", "mtm_alias", "cabang", "grup_brand", "item"
    "metric_type": "idr",
    "month": "2025-12",
    "mtm_type": "KA"
  }
  ```
- **Response**: Array of Pareto items sorted descending by contribution value with cumulative percentage.

### G. Analytics - Detail Transaction Grid
- **Endpoint**: `POST /api/analytics/grid`
- **Response**: List of transaction records matching active filters.
