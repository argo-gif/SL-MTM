import time
import zipfile
import re
import sqlite3
import os

def hyper_fast_ingest(xlsx_path, target_month, db_path=None):
    t0 = time.time()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = db_path if db_path else os.path.join(base_dir, "dataset.db")
    target_month = str(target_month).strip()

    print(f"[{time.strftime('%H:%M:%S')}] Hyper-fast ingest starting for {xlsx_path} (Target: {target_month})...")

    with zipfile.ZipFile(xlsx_path, 'r') as z:
        # 1. Parse Shared Strings using fast regex
        t_ss = time.time()
        ss = []
        if 'xl/sharedStrings.xml' in z.namelist():
            ss_bytes = z.read('xl/sharedStrings.xml')
            # Extract text elements
            ss = [m.decode('utf-8', errors='ignore') for m in re.findall(b'<t[^>]*>(.*?)</t>', ss_bytes)]
        print(f"[{time.strftime('%H:%M:%S')}] Shared strings ({len(ss):,} entries) parsed in {time.time()-t_ss:.2f}s")

        # 2. Open Sheet XML stream
        t_sheet = time.time()
        sheet_name = 'xl/worksheets/sheet1.xml'
        if sheet_name not in z.namelist():
            for name in z.namelist():
                if name.startswith('xl/worksheets/sheet'):
                    sheet_name = name
                    break

        sheet_bytes = z.read(sheet_name)
        print(f"[{time.strftime('%H:%M:%S')}] Sheet XML ({len(sheet_bytes):,} bytes) read in {time.time()-t_sheet:.2f}s")

        # 3. Fast Row-by-Row parsing using regex matching per row
        t_parse = time.time()
        # Find cell pattern: cell ref, type, val
        # <c r="A1" t="s"><v>0</v></c> or <c r="B1"><v>12.34</v></c>
        c_pattern = re.compile(b'<c r="([A-Z]+)(\\d+)"(?: t="([^"]+)")?>(?:<f.*?</f>)?<v>(.*?)</v></c>')

        # Header mapping
        header_indices = {}
        rows = []
        month_counts = {}

        # Split XML by <row> tags
        row_chunks = sheet_bytes.split(b'<row ')
        print(f"[{time.strftime('%H:%M:%S')}] Split into {len(row_chunks):,} row chunks in {time.time()-t_parse:.2f}s")

        t_rows = time.time()
        for chunk in row_chunks[1:]:
            cells = c_pattern.findall(chunk)
            if not cells:
                continue

            row_num = int(cells[0][1])
            row_dict = {}

            for col_b, rnum_b, ttype_b, val_b in cells:
                col_let = col_b.decode('utf-8')
                val_str = val_b.decode('utf-8', errors='ignore')

                if ttype_b == b's' and val_str.isdigit():
                    s_idx = int(val_str)
                    val_str = ss[s_idx] if s_idx < len(ss) else val_str

                row_dict[col_let] = val_str

            if row_num == 1:
                # Map column letters to field names
                for col_let, val in row_dict.items():
                    hu = str(val).upper().strip()
                    if hu in ['DELIVERY_DATE', 'TGL_NP', 'TGL KIRIM']: header_indices[col_let] = 'delivery_date'
                    elif hu in ['JENIS MTM', 'JENIS_MTM']: header_indices[col_let] = 'mtm_type'
                    elif hu in ['BRANCH_NAME', 'CABANG']: header_indices[col_let] = 'branch'
                    elif hu in ['MTM_ALIAS', 'MTM ALIAS']: header_indices[col_let] = 'mtm_alias'
                    elif hu in ['GROUP BRAND', 'GRUP BRAND', 'GROUP_BRAND']: header_indices[col_let] = 'brand_group'
                    elif hu in ['PRODUCT_CODE', 'KODE ITEM', 'KODE_ITEM']: header_indices[col_let] = 'product_code'
                    elif hu in ['PRODUCT_NAME', 'NAMA ITEM', 'ITEM']: header_indices[col_let] = 'item_name'
                    elif hu in ['ALASAN_TIDAK_TERKIRIM', 'ALASAN KIRIM']: header_indices[col_let] = 'reason_kirim'
                    elif hu in ['ALASAN_REALISASI']: header_indices[col_let] = 'reason_realisasi'
                    elif hu in ['R_KIRIM', 'NOMINAL KIRIM']: header_indices[col_let] = 'idr_kirim'
                    elif hu in ['RP_REALISASI', 'NOMINAL REALISASI']: header_indices[col_let] = 'idr_realisasi'
                    elif hu in ['R_PESAN', 'NOMINAL PESAN']: header_indices[col_let] = 'idr_pesan'
                    elif hu in ['QTY_DELIVERY_IN_SMALLEST_UNIT', 'QTY KIRIM']: header_indices[col_let] = 'qty_kirim'
                    elif hu in ['QTY_REALISASI']: header_indices[col_let] = 'qty_realisasi'
                    elif hu in ['QTY_ORDER_IN_SMALLEST_UNIT', 'QTY ORDER']: header_indices[col_let] = 'qty_order'
            else:
                rec = {header_indices[col]: val for col, val in row_dict.items() if col in header_indices}
                if not rec:
                    continue

                dt = rec.get('delivery_date', '').strip()
                if len(dt) >= 10 and '-' in dt: month = dt[:7]
                elif len(dt) >= 6 and dt[:6].isdigit(): month = f"{dt[:4]}-{dt[4:6]}"
                elif len(dt) >= 7 and dt[:4].isdigit(): month = dt[:7]
                else: month = target_month

                if month:
                    month_counts[month] = month_counts.get(month, 0) + 1

                rk = rec.get('reason_kirim', '').strip()
                rr = rec.get('reason_realisasi', '').strip()
                if rk != "" and rr == "": reason_final = rk
                elif rk == "" and rr != "": reason_final = rr
                elif rk != "" and rr != "": reason_final = rk
                else: reason_final = 'On-Time / Sesuai'

                mtm_type = rec.get('mtm_type', 'Unclassified').strip() or 'Unclassified'
                branch = rec.get('branch', 'Unclassified').strip() or 'Unclassified'
                mtm_alias = rec.get('mtm_alias', 'Unclassified').strip() or 'Unclassified'
                brand_group = rec.get('brand_group', 'Unclassified').strip() or 'Unclassified'
                p_code = rec.get('product_code', '').strip()
                item_name = rec.get('item_name', 'Unclassified').strip() or 'Unclassified'
                item_display = f"{p_code} - {item_name}" if p_code else item_name

                try: idr_k = float(rec.get('idr_kirim') or 0)
                except: idr_k = 0.0
                try: idr_r = float(rec.get('idr_realisasi') or 0)
                except: idr_r = 0.0
                try: idr_p = float(rec.get('idr_pesan') or 0)
                except: idr_p = 0.0
                try: qty_k = float(rec.get('qty_kirim') or 0)
                except: qty_k = 0.0
                try: qty_r = float(rec.get('qty_realisasi') or 0)
                except: qty_r = 0.0
                try: qty_o = float(rec.get('qty_order') or 0)
                except: qty_o = 0.0

                rows.append((
                    dt, month, mtm_type, branch, mtm_alias, brand_group, p_code, item_name, item_display,
                    rk, rr, reason_final, idr_k, idr_r, idr_p, qty_k, qty_r, qty_o
                ))

        print(f"[{time.strftime('%H:%M:%S')}] Parsed {len(rows):,} rows in {time.time()-t_rows:.2f}s")
        print("Detected month breakdown:", month_counts)
        print(f"[{time.strftime('%H:%M:%S')}] Total Ingest Time: {time.time()-t0:.2f} seconds!")

if __name__ == "__main__":
    hyper_fast_ingest("uploaded_active_dataset.xlsx", "2026-08")
