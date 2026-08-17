import zipfile
import xml.etree.ElementTree as ET
import sqlite3
import time
import os

def build_db(xlsx_path=None, db_path=None):
    start = time.time()
    base_dir = os.path.dirname(os.path.abspath(__file__))
    root_dir = os.path.dirname(base_dir)

    xlsx_path = xlsx_path if xlsx_path else os.path.join(root_dir, "uploaded_active_dataset.xlsx")
    db_path = db_path if db_path else os.path.join(base_dir, "dataset.db")

    print(f"Building SQLite database from {xlsx_path} via streaming iterparse...", flush=True)

    if os.path.exists(db_path):
        try: os.remove(db_path)
        except Exception as e: print("Remove DB notice:", e, flush=True)

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    cur.execute("PRAGMA synchronous = OFF;")
    cur.execute("PRAGMA journal_mode = MEMORY;")

    cur.execute('''
        CREATE TABLE IF NOT EXISTS dataset (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            delivery_date TEXT,
            month TEXT,
            mtm_type TEXT,
            branch TEXT,
            mtm_alias TEXT,
            brand_group TEXT,
            product_code TEXT,
            item_name TEXT,
            item_display TEXT,
            reason_kirim TEXT,
            reason_realisasi TEXT,
            reason_final TEXT,
            idr_kirim REAL,
            idr_realisasi REAL,
            idr_pesan REAL,
            qty_kirim REAL,
            qty_realisasi REAL,
            qty_order REAL
        )

    ''')

    with zipfile.ZipFile(xlsx_path, 'r') as z:
        # 1. Parse Shared Strings
        print("Reading sharedStrings.xml...", flush=True)
        ss_file = z.open('xl/sharedStrings.xml')
        shared_strings = []
        for event, elem in ET.iterparse(ss_file, events=('end',)):
            if elem.tag.endswith('t'):
                shared_strings.append(elem.text or '')
                elem.clear()
        print(f"Loaded {len(shared_strings):,} shared strings in {time.time() - start:.2f}s", flush=True)

        # 2. Parse Sheet1
        sheet_path = 'xl/worksheets/sheet1.xml'
        if sheet_path not in z.namelist():
            for name in z.namelist():
                if name.startswith('xl/worksheets/sheet'):
                    sheet_path = name
                    break

        print(f"Streaming worksheet {sheet_path}...", flush=True)
        sheet_file = z.open(sheet_path)

        header_map = {}
        batch = []
        total_rows = 0

        context = ET.iterparse(sheet_file, events=('end',))
        for event, elem in context:
            if elem.tag.endswith('row'):
                r_num = elem.attrib.get('r')
                
                # Extract cells for this row
                row_cells = {}
                for cell in elem:
                    if cell.tag.endswith('c'):
                        cell_ref = cell.attrib.get('r', '')
                        col_let = ''.join([ch for ch in cell_ref if ch.isalpha()])
                        t_type = cell.attrib.get('t', '')
                        
                        v_elem = cell.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                        if v_elem is not None and v_elem.text is not None:
                            val = v_elem.text
                            if t_type == 's' and val.isdigit():
                                idx = int(val)
                                val = shared_strings[idx] if idx < len(shared_strings) else val
                        else:
                            val = ''
                            
                        row_cells[col_let] = val

                if r_num == '1':
                    print("Row 1 Headers:", row_cells, flush=True)
                    for col_let, val in row_cells.items():
                        hu = str(val).upper().strip()
                        if hu == 'DELIVERY_DATE' or hu == 'TGL_NP' or hu == 'TGL KIRIM': header_map[col_let] = 'delivery_date'
                        elif hu == 'JENIS MTM' or hu == 'JENIS_MTM': header_map[col_let] = 'mtm_type'
                        elif hu == 'BRANCH_NAME' or hu == 'CABANG': header_map[col_let] = 'branch'
                        elif hu == 'MTM_ALIAS' or hu == 'MTM ALIAS': header_map[col_let] = 'mtm_alias'
                        elif hu == 'GROUP BRAND' or hu == 'GRUP BRAND' or hu == 'GROUP_BRAND': header_map[col_let] = 'brand_group'
                        elif hu == 'PRODUCT_CODE' or hu == 'KODE ITEM' or hu == 'KODE_ITEM': header_map[col_let] = 'product_code'
                        elif hu == 'PRODUCT_NAME' or hu == 'NAMA ITEM' or hu == 'ITEM': header_map[col_let] = 'item_name'
                        elif hu == 'ALASAN_TIDAK_TERKIRIM' or hu == 'ALASAN KIRIM': header_map[col_let] = 'reason_kirim'
                        elif hu == 'ALASAN_REALISASI': header_map[col_let] = 'reason_realisasi'
                        elif hu == 'R_KIRIM' or hu == 'NOMINAL KIRIM': header_map[col_let] = 'idr_kirim'
                        elif hu == 'RP_REALISASI' or hu == 'NOMINAL REALISASI': header_map[col_let] = 'idr_realisasi'
                        elif hu == 'R_PESAN' or hu == 'NOMINAL PESAN': header_map[col_let] = 'idr_pesan'
                        elif hu == 'QTY_DELIVERY_IN_SMALLEST_UNIT' or hu == 'QTY KIRIM': header_map[col_let] = 'qty_kirim'
                        elif hu == 'QTY_REALISASI': header_map[col_let] = 'qty_realisasi'
                        elif hu == 'QTY_ORDER_IN_SMALLEST_UNIT' or hu == 'QTY ORDER': header_map[col_let] = 'qty_order'

                    print("Header Map:", header_map, flush=True)
                else:
                    rec = {}
                    for col_let, val in row_cells.items():
                        fname = header_map.get(col_let)
                        if fname:
                            rec[fname] = val

                    rk = str(rec.get('reason_kirim') or '').strip()
                    rr = str(rec.get('reason_realisasi') or '').strip()
                    if rk != "" and rr == "": reason_final = rk
                    elif rk == "" and rr != "": reason_final = rr
                    elif rk != "" and rr != "": reason_final = rk
                    else: reason_final = 'On-Time / Sesuai'

                    dt = str(rec.get('delivery_date') or '').strip()
                    if len(dt) >= 10 and '-' in dt: month = dt[:7]
                    elif len(dt) >= 6 and dt[:6].isdigit(): month = f"{dt[:4]}-{dt[4:6]}"
                    elif len(dt) >= 7 and dt[:4].isdigit(): month = dt[:7]
                    else: month = '2026-01'

                    mtm_type = str(rec.get('mtm_type') or 'Unclassified').strip()
                    branch = str(rec.get('branch') or 'Unclassified').strip()
                    mtm_alias = str(rec.get('mtm_alias') or 'Unclassified').strip()
                    brand_group = str(rec.get('brand_group') or 'Unclassified').strip()
                    p_code = str(rec.get('product_code') or '').strip()
                    item_name = str(rec.get('item_name') or 'Unclassified').strip()
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

                    batch.append((
                        dt, month, mtm_type, branch, mtm_alias, brand_group, p_code, item_name, item_display,
                        rk, rr, reason_final, idr_k, idr_r, idr_p, qty_k, qty_r, qty_o
                    ))
                    total_rows += 1

                    if len(batch) >= 20000:
                        cur.executemany('''
                            INSERT INTO dataset (
                                delivery_date, month, mtm_type, branch, mtm_alias, brand_group, product_code, item_name, item_display,
                                reason_kirim, reason_realisasi, reason_final,
                                idr_kirim, idr_realisasi, idr_pesan, qty_kirim, qty_realisasi, qty_order
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        ''', batch)
                        conn.commit()
                        batch = []
                        print(f"  Processed {total_rows:,} rows...", flush=True)

                elem.clear()

        if batch:
            cur.executemany('''
                INSERT INTO dataset (
                    delivery_date, month, mtm_type, branch, mtm_alias, brand_group, product_code, item_name, item_display,
                    reason_kirim, reason_realisasi, reason_final,
                    idr_kirim, idr_realisasi, idr_pesan, qty_kirim, qty_realisasi, qty_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', batch)
            conn.commit()

        print("Building indexes for instant query performance...", flush=True)
        cur.execute("CREATE INDEX IF NOT EXISTS idx_month ON dataset(month);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mtm_type ON dataset(mtm_type);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_branch ON dataset(branch);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_mtm_alias ON dataset(mtm_alias);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_brand_group ON dataset(brand_group);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_item_display ON dataset(item_display);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_reason ON dataset(reason_final);")
        conn.commit()


        cur.execute("SELECT COUNT(*) FROM dataset;")
        db_cnt = cur.fetchone()[0]
        print(f"SUCCESS! Created SQLite Database with {db_cnt:,} rows in {time.time() - start:.2f} seconds.", flush=True)

    conn.close()

if __name__ == "__main__":
    build_db()
