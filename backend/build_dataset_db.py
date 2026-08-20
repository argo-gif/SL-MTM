import zipfile
import sqlite3
import time
import re
import os

def build_sqlite_db(xlsx_path="uploaded_active_dataset.xlsx", db_path="backend/dataset.db"):
    start = time.time()
    print(f"Building SQLite DB cache from {xlsx_path}...")

    if os.path.exists(db_path):
        try: os.remove(db_path)
        except Exception: pass

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    cur.execute("PRAGMA synchronous = OFF;")
    cur.execute("PRAGMA journal_mode = MEMORY;")

    # Create Table
    cur.execute('DROP TABLE IF EXISTS dataset;')
    cur.execute('''
        CREATE TABLE dataset (

            id INTEGER PRIMARY KEY AUTOINCREMENT,
            delivery_date TEXT,
            month TEXT,
            mtm_type TEXT,
            branch TEXT,
            mtm_alias TEXT,
            brand_group TEXT,
            item_name TEXT,
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
        print("Reading shared strings...")
        ss_bytes = z.read('xl/sharedStrings.xml')
        shared_strings = re.findall(r'<t[^>]*>(.*?)</t>', ss_bytes.decode('utf-8', errors='ignore'), re.DOTALL)
        print(f"Loaded {len(shared_strings)} shared strings in {time.time() - start:.2f}s")

        sheet_path = 'xl/worksheets/sheet1.xml'
        if sheet_path not in z.namelist():
            for name in z.namelist():
                if name.startswith('xl/worksheets/sheet'):
                    sheet_path = name
                    break

        print(f"Streaming sheet {sheet_path}...")
        sheet_content = z.read(sheet_path).decode('utf-8', errors='ignore')

        header_map = {}
        batch = []
        cell_regex = re.compile(r'<c r="([A-Z]+)(\d+)"[^>]*(?:t="([^"]+)")?[^>]*>(?:<v>(.*?)</v>)?', re.DOTALL)
        row_regex = re.compile(r'<row r="(\d+)"[^>]*>(.*?)</row>', re.DOTALL)

        count = 0
        for match in row_regex.finditer(sheet_content):
            r_num = match.group(1)
            row_inner = match.group(2)
            
            row_dict = {}
            for c_match in cell_regex.finditer(row_inner):
                col_let = c_match.group(1)
                t_attr = c_match.group(3)
                val = c_match.group(4) or ''
                if t_attr == 's' and val != '' and val.isdigit():
                    idx = int(val)
                    val = shared_strings[idx] if idx < len(shared_strings) else val
                row_dict[col_let] = val

            if r_num == '1':
                for col_let, val in row_dict.items():
                    hu = str(val).upper().strip()
                    if 'DELIVERY_DATE' in hu or 'TGL' in hu: header_map[col_let] = 'delivery_date'
                    elif 'JENIS MTM' in hu or 'JENIS_MTM' in hu: header_map[col_let] = 'mtm_type'
                    elif 'BRANCH_NAME' in hu or 'CABANG' in hu: header_map[col_let] = 'branch'
                    elif 'MTM_ALIAS' in hu or 'MTM ALIAS' in hu: header_map[col_let] = 'mtm_alias'
                    elif 'GROUP BRAND' in hu or 'GRUP BRAND' in hu: header_map[col_let] = 'brand_group'
                    elif 'PRODUCT_NAME' in hu or 'NAMA ITEM' in hu or 'ITEM' in hu: header_map[col_let] = 'item_name'
                    elif 'ALASAN_TIDAK_TERKIRIM' in hu or 'ALASAN KIRIM' in hu: header_map[col_let] = 'reason_kirim'
                    elif 'ALASAN_REALISASI' in hu: header_map[col_let] = 'reason_realisasi'
                    elif 'R_KIRIM' in hu: header_map[col_let] = 'idr_kirim'
                    elif 'RP_REALISASI' in hu: header_map[col_let] = 'idr_realisasi'
                    elif 'R_PESAN' in hu: header_map[col_let] = 'idr_pesan'
                    elif 'QTY_DELIVERY' in hu or 'QTY KIRIM' in hu: header_map[col_let] = 'qty_kirim'
                    elif 'QTY_REALISASI' in hu: header_map[col_let] = 'qty_realisasi'
                    elif 'QTY_ORDER' in hu: header_map[col_let] = 'qty_order'
            else:
                rec = {}
                for col_let, val in row_dict.items():
                    fname = header_map.get(col_let)
                    if fname:
                        rec[fname] = val

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

                rk = str(rec.get('reason_kirim') or '').strip()
                rr = str(rec.get('reason_realisasi') or '').strip()
                if rk != "" and rr == "": reason_final = rk
                elif rk == "" and rr != "": reason_final = rr
                elif rk != "" and rr != "": reason_final = rk
                else: reason_final = 'On-Time / Sesuai'

                dt = str(rec.get('delivery_date') or '').strip()
                if len(dt) >= 10 and '-' in dt:
                    month = dt[:7]
                elif len(dt) >= 6 and dt[:6].isdigit():
                    month = f"{dt[:4]}-{dt[4:6]}"
                elif len(dt) >= 7 and dt[:4].isdigit():
                    month = dt[:7]
                else:
                    month = '2026-01'


                mtm_type = str(rec.get('mtm_type') or 'KA').strip()
                branch = str(rec.get('branch') or 'Unclassified').strip()
                mtm_alias = str(rec.get('mtm_alias') or 'Unclassified').strip()
                brand_group = str(rec.get('brand_group') or 'Unclassified').strip()
                item_name = str(rec.get('item_name') or 'Unclassified').strip()

                batch.append((
                    dt, month, mtm_type, branch, mtm_alias, brand_group, item_name,
                    rk, rr, reason_final, idr_k, idr_r, idr_p, qty_k, qty_r, qty_o
                ))
                count += 1

                if len(batch) >= 15000:
                    cur.executemany('''
                        INSERT INTO dataset (
                            delivery_date, month, mtm_type, branch, mtm_alias, brand_group, item_name,
                            reason_kirim, reason_realisasi, reason_final,
                            idr_kirim, idr_realisasi, idr_pesan, qty_kirim, qty_realisasi, qty_order
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', batch)
                    conn.commit()
                    batch = []
                    print(f"Processed {count:,} rows...")

        if batch:
            cur.executemany('''
                INSERT INTO dataset (
                    delivery_date, month, mtm_type, branch, mtm_alias, brand_group, item_name,
                    reason_kirim, reason_realisasi, reason_final,
                    idr_kirim, idr_realisasi, idr_pesan, qty_kirim, qty_realisasi, qty_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', batch)
            conn.commit()

        print("Building indexes for instant filtering (< 5ms)...")
        cur.execute("CREATE INDEX idx_month ON dataset(month);")
        cur.execute("CREATE INDEX idx_mtm_type ON dataset(mtm_type);")
        cur.execute("CREATE INDEX idx_branch ON dataset(branch);")
        cur.execute("CREATE INDEX idx_mtm_alias ON dataset(mtm_alias);")
        cur.execute("CREATE INDEX idx_brand_group ON dataset(brand_group);")
        cur.execute("CREATE INDEX idx_reason ON dataset(reason_final);")
        conn.commit()

        cur.execute("SELECT COUNT(*) FROM dataset;")
        total = cur.fetchone()[0]
        print(f"SUCCESS! Database created with {total:,} rows in {time.time() - start:.2f} seconds.")

    conn.close()

if __name__ == "__main__":
    build_sqlite_db()
