import time
import zipfile
import xml.parsers.expat
import os

def test_expat_fast(xlsx_path, target_month):
    t0 = time.time()
    print(f"Expat fast loader benchmark starting for {xlsx_path}...")

    with zipfile.ZipFile(xlsx_path, 'r') as z:
        # 1. Shared Strings with Expat
        t_ss = time.time()
        ss = []
        in_t = False
        cur_text = []

        def ss_start(name, attrs):
            nonlocal in_t, cur_text
            if name == 't':
                in_t = True
                cur_text = []

        def ss_char(data):
            if in_t:
                cur_text.append(data)

        def ss_end(name):
            nonlocal in_t
            if name == 't':
                in_t = False
                ss.append(''.join(cur_text))

        p_ss = xml.parsers.expat.ParserCreate()
        p_ss.StartElementHandler = ss_start
        p_ss.CharacterDataHandler = ss_char
        p_ss.EndElementHandler = ss_end

        if 'xl/sharedStrings.xml' in z.namelist():
            p_ss.Parse(z.read('xl/sharedStrings.xml'))
        print(f"Shared strings ({len(ss):,} entries) parsed in {time.time()-t_ss:.2f}s")

        # 2. Sheet rows with Expat
        t_sheet = time.time()
        sheet_name = 'xl/worksheets/sheet1.xml'
        if sheet_name not in z.namelist():
            for name in z.namelist():
                if name.startswith('xl/worksheets/sheet'):
                    sheet_name = name
                    break

        header_map = {}
        rows = []
        month_counts = {}

        cur_row = None
        cur_cell = None
        cur_val = []
        is_shared = False

        def sheet_start(name, attrs):
            nonlocal cur_row, cur_cell, cur_val, is_shared
            if name == 'row':
                cur_row = int(attrs.get('r', 0))
            elif name == 'c':
                ref = attrs.get('r', '')
                col_let = ''.join([ch for ch in ref if ch.isalpha()])
                is_shared = (attrs.get('t') == 's')
                cur_cell = col_let
                cur_val = []
            elif name == 'v':
                cur_val = []

        def sheet_char(data):
            if cur_cell:
                cur_val.append(data)

        def sheet_end(name):
            nonlocal cur_row, cur_cell, cur_val, is_shared
            if name == 'c':
                val_str = ''.join(cur_val).strip()
                if is_shared and val_str.isdigit():
                    idx = int(val_str)
                    val_str = ss[idx] if idx < len(ss) else val_str
                
                if cur_row == 1:
                    hu = val_str.upper().strip()
                    if hu in ['DELIVERY_DATE', 'TGL_NP', 'TGL KIRIM']: header_map[cur_cell] = 'delivery_date'
                    elif hu in ['JENIS MTM', 'JENIS_MTM']: header_map[cur_cell] = 'mtm_type'
                    elif hu in ['BRANCH_NAME', 'CABANG']: header_map[cur_cell] = 'branch'
                    elif hu in ['MTM_ALIAS', 'MTM ALIAS']: header_map[cur_cell] = 'mtm_alias'
                    elif hu in ['GROUP BRAND', 'GRUP BRAND', 'GROUP_BRAND']: header_map[cur_cell] = 'brand_group'
                    elif hu in ['PRODUCT_CODE', 'KODE ITEM', 'KODE_ITEM']: header_map[cur_cell] = 'product_code'
                    elif hu in ['PRODUCT_NAME', 'NAMA ITEM', 'ITEM']: header_map[cur_cell] = 'item_name'
                    elif hu in ['ALASAN_TIDAK_TERKIRIM', 'ALASAN KIRIM']: header_map[cur_cell] = 'reason_kirim'
                    elif hu in ['ALASAN_REALISASI']: header_map[cur_cell] = 'reason_realisasi'
                    elif hu in ['R_KIRIM', 'NOMINAL KIRIM']: header_map[cur_cell] = 'idr_kirim'
                    elif hu in ['RP_REALISASI', 'NOMINAL REALISASI']: header_map[cur_cell] = 'idr_realisasi'
                    elif hu in ['R_PESAN', 'NOMINAL PESAN']: header_map[cur_cell] = 'idr_pesan'
                    elif hu in ['QTY_DELIVERY_IN_SMALLEST_UNIT', 'QTY KIRIM']: header_map[cur_cell] = 'qty_kirim'
                    elif hu in ['QTY_REALISASI']: header_map[cur_cell] = 'qty_realisasi'
                    elif hu in ['QTY_ORDER_IN_SMALLEST_UNIT', 'QTY ORDER']: header_map[cur_cell] = 'qty_order'
                elif cur_row and cur_row > 1:
                    # store cell in active row dict
                    active_row[cur_cell] = val_str
                cur_cell = None

            elif name == 'row':
                if cur_row and cur_row > 1 and active_row:
                    rec = {header_map[col]: val for col, val in active_row.items() if col in header_map}
                    if rec:
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
                    active_row.clear()

        p_sheet = xml.parsers.expat.ParserCreate()
        p_sheet.StartElementHandler = sheet_start
        p_sheet.CharacterDataHandler = sheet_char
        p_sheet.EndElementHandler = sheet_end

        active_row = {}

        # Stream chunk by chunk for minimal RAM
        with z.open(sheet_name) as f:
            while True:
                chunk = f.read(65536)
                if not chunk:
                    break
                p_sheet.Parse(chunk)

        print(f"Expat parsed {len(rows):,} rows in {time.time()-t_sheet:.2f}s! Total: {time.time()-t0:.2f}s")
        print("Detected months:", month_counts)

if __name__ == "__main__":
    test_expat_fast("uploaded_active_dataset.xlsx", "2026-08")
