import time
import zipfile
import re
import sqlite3
import os

def benchmark_regex_ultra(xlsx_path, target_month):
    t0 = time.time()
    print(f"Regex Ultra Speed Benchmark for {xlsx_path}...")

    with zipfile.ZipFile(xlsx_path, 'r') as z:
        # 1. Parse Shared Strings using C-regex
        t_ss = time.time()
        ss = []
        if 'xl/sharedStrings.xml' in z.namelist():
            ss_bytes = z.read('xl/sharedStrings.xml')
            ss_matches = re.findall(b'<t[^>]*>(.*?)</t>', ss_bytes)
            ss = [m.decode('utf-8', errors='ignore') for m in ss_matches]
        print(f"Shared strings ({len(ss):,} entries) parsed in {time.time()-t_ss:.2f}s")

        # 2. Parse Sheet XML
        t_sheet = time.time()
        sheet_name = 'xl/worksheets/sheet1.xml'
        if sheet_path := next((n for n in z.namelist() if n.startswith('xl/worksheets/sheet')), None):
            sheet_name = sheet_path

        header_map = {}
        rows = []
        month_counts = {}

        # Regex patterns compiled in C
        row_pattern = re.compile(b'<row r="(\d+)"[^>]*>(.*?)</row>', re.DOTALL)
        cell_pattern = re.compile(b'<c r="([A-Z]+)\d+"(?: t="([^"]+)")?[^>]*>(?:<v>(.*?)</v>)?', re.DOTALL)

        # Stream chunking by row
        with z.open(sheet_name) as f:
            buffer = b''
            row_idx = 0
            while True:
                chunk = f.read(524288) # Read 512KB chunks
                if not chunk:
                    if buffer:
                        # Process remaining buffer
                        for m_row in row_pattern.finditer(buffer):
                            r_num = int(m_row.group(1))
                            r_xml = m_row.group(2)
                            _process_row(r_num, r_xml, cell_pattern, ss, header_map, target_month, month_counts, rows)
                    break
                
                buffer += chunk
                last_row_end = buffer.rfind(b'</row>')
                if last_row_end != -1:
                    slice_xml = buffer[:last_row_end+6]
                    buffer = buffer[last_row_end+6:]
                    for m_row in row_pattern.finditer(slice_xml):
                        r_num = int(m_row.group(1))
                        r_xml = m_row.group(2)
                        _process_row(r_num, r_xml, cell_pattern, ss, header_map, target_month, month_counts, rows)

        print(f"Parsed {len(rows):,} rows in {time.time()-t_sheet:.2f}s! Total time: {time.time()-t0:.2f}s")
        print("Month Breakdown:", month_counts)

def _process_row(r_num, r_xml, cell_pattern, ss, header_map, target_month, month_counts, rows):
    row_cells = {}
    for m_cell in cell_pattern.finditer(r_xml):
        col_let = m_cell.group(1).decode('ascii')
        t_type = m_cell.group(2)
        v_bytes = m_cell.group(3)

        val = ''
        if v_bytes:
            v_str = v_bytes.decode('utf-8', errors='ignore').strip()
            if t_type == b's' and v_str.isdigit():
                idx = int(v_str)
                val = ss[idx] if idx < len(ss) else v_str
            else:
                val = v_str
        row_cells[col_let] = val

    if r_num == 1:
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
        rec = {header_map[col]: val for col, val in row_cells.items() if col in header_map}
        if rec:
            dt = str(rec.get('delivery_date') or '').strip()
            if len(dt) >= 10 and '-' in dt: month = dt[:7]
            elif len(dt) >= 6 and dt[:6].isdigit(): month = f"{dt[:4]}-{dt[4:6]}"
            elif len(dt) >= 7 and dt[:4].isdigit(): month = dt[:7]
            else: month = ''

            if month:
                month_counts[month] = month_counts.get(month, 0) + 1

            rk = str(rec.get('reason_kirim') or '').strip()
            rr = str(rec.get('reason_realisasi') or '').strip()
            if rk != "" and rr == "": reason_final = rk
            elif rk == "" and rr != "": reason_final = rr
            elif rk != "" and rr != "": reason_final = rk
            else: reason_final = 'On-Time / Sesuai'

            mtm_type = str(rec.get('mtm_type') or 'Unclassified').strip() or 'Unclassified'
            branch = str(rec.get('branch') or 'Unclassified').strip() or 'Unclassified'
            mtm_alias = str(rec.get('mtm_alias') or 'Unclassified').strip() or 'Unclassified'
            brand_group = str(rec.get('brand_group') or 'Unclassified').strip() or 'Unclassified'
            p_code = str(rec.get('product_code') or '').strip()
            item_name = str(rec.get('item_name') or 'Unclassified').strip() or 'Unclassified'
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

if __name__ == "__main__":
    benchmark_regex_ultra("uploaded_active_dataset.xlsx", "2026-08")
