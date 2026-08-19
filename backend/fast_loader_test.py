import time
import zipfile
import re
import os
import sqlite3

def benchmark_fast_loader(xlsx_path):
    start = time.time()
    print(f"Starting fast loader benchmark on {xlsx_path}...")

    with zipfile.ZipFile(xlsx_path, 'r') as z:
        # 1. Parse Shared Strings
        t0 = time.time()
        ss_bytes = z.read('xl/sharedStrings.xml') if 'xl/sharedStrings.xml' in z.namelist() else b''
        ss_matches = re.findall(b'<t[^>]*>(.*?)</t>', ss_bytes)
        shared_strings = [m.decode('utf-8', errors='ignore') for m in ss_matches]
        print(f"Shared strings parsed: {len(shared_strings):,} in {time.time()-t0:.2f}s")

        # 2. Parse Sheet XML
        t1 = time.time()
        sheet_path = 'xl/worksheets/sheet1.xml'
        if sheet_path not in z.namelist():
            for name in z.namelist():
                if name.startswith('xl/worksheets/sheet'):
                    sheet_path = name
                    break

        sheet_bytes = z.read(sheet_path)
        print(f"Sheet XML read ({len(sheet_bytes):,} bytes) in {time.time()-t1:.2f}s")

        # 3. Regex Row Parsing
        t2 = time.time()
        # Find cell pattern: col, type, val
        # <c r="A1" t="s"><v>0</v></c> or <c r="B1"><v>123.45</v></c>
        cell_regex = re.compile(br'<c r="([A-Z]+)(\d+)"(?: t="([^"]+)")?>(?:<f.*?</f>)?<v>(.*?)</v></c>')

        header_map = {}
        rows = []
        month_counts = {}

        # Split into row blocks
        row_blocks = sheet_bytes.split(b'</row>')
        print(f"Row blocks split: {len(row_blocks):,} in {time.time()-t2:.2f}s")

        t3 = time.time()
        for block in row_blocks:
            if not block or b'<row' not in block:
                continue

            matches = cell_regex.findall(block)
            if not matches:
                continue

            row_num = matches[0][1].decode('utf-8')
            row_cells = {}

            for col_bytes, rnum_bytes, ttype_bytes, val_bytes in matches:
                col_let = col_bytes.decode('utf-8')
                val = val_bytes.decode('utf-8', errors='ignore')

                if ttype_bytes == b's' and val.isdigit():
                    idx = int(val)
                    val = shared_strings[idx] if idx < len(shared_strings) else val

                row_cells[col_let] = val

            if row_num == '1':
                for col_let, val in row_cells.items():
                    hu = str(val).upper().strip()
                    if hu in ['DELIVERY_DATE', 'TGL_NP', 'TGL KIRIM']: header_map[col_let] = 'delivery_date'
                    elif hu in ['JENIS MTM', 'JENIS_MTM']: header_map[col_let] = 'mtm_type'
                    elif hu in ['BRANCH_NAME', 'CABANG']: header_map[col_let] = 'branch'
                    elif hu in ['MTM_ALIAS', 'MTM ALIAS']: header_map[col_let] = 'mtm_alias'
                    elif hu in ['GROUP BRAND', 'GRUP BRAND', 'GROUP_BRAND']: header_map[col_let] = 'brand_group'
                    elif hu in ['PRODUCT_CODE', 'KODE ITEM', 'KODE_ITEM']: header_map[col_let] = 'product_code'
                    elif hu in ['PRODUCT_NAME', 'NAMA ITEM', 'ITEM']: header_map[col_let] = 'item_name'
                    elif hu in ['ALASAN_TIDAK_TERKIRIM', 'ALASAN KIRIM']: header_map[col_let] = 'reason_kirim'
                    elif hu in ['ALASAN_REALISASI']: header_map[col_let] = 'reason_realisasi'
                    elif hu in ['R_KIRIM', 'NOMINAL KIRIM']: header_map[col_let] = 'idr_kirim'
                    elif hu in ['RP_REALISASI', 'NOMINAL REALISASI']: header_map[col_let] = 'idr_realisasi'
                    elif hu in ['R_PESAN', 'NOMINAL PESAN']: header_map[col_let] = 'idr_pesan'
                    elif hu in ['QTY_DELIVERY_IN_SMALLEST_UNIT', 'QTY KIRIM']: header_map[col_let] = 'qty_kirim'
                    elif hu in ['QTY_REALISASI']: header_map[col_let] = 'qty_realisasi'
                    elif hu in ['QTY_ORDER_IN_SMALLEST_UNIT', 'QTY ORDER']: header_map[col_let] = 'qty_order'
            else:
                rec = {header_map[col_let]: val for col_let, val in row_cells.items() if col_let in header_map}
                if not rec:
                    continue

                rk = rec.get('reason_kirim', '').strip()
                rr = rec.get('reason_realisasi', '').strip()
                if rk != "" and rr == "": reason_final = rk
                elif rk == "" and rr != "": reason_final = rr
                elif rk != "" and rr != "": reason_final = rk
                else: reason_final = 'On-Time / Sesuai'

                dt = rec.get('delivery_date', '').strip()
                if len(dt) >= 10 and '-' in dt: month = dt[:7]
                elif len(dt) >= 6 and dt[:6].isdigit(): month = f"{dt[:4]}-{dt[4:6]}"
                elif len(dt) >= 7 and dt[:4].isdigit(): month = dt[:7]
                else: month = '2026-08'

                if month:
                    month_counts[month] = month_counts.get(month, 0) + 1

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

        print(f"Parsed {len(rows):,} rows in {time.time()-t3:.2f}s. Total time: {time.time()-start:.2f}s")
        print("Detected months:", month_counts)

if __name__ == "__main__":
    benchmark_fast_loader("uploaded_active_dataset.xlsx")
