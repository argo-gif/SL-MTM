import time
import zipfile
import xml.etree.ElementTree as ET

def benchmark_positional(xlsx_path):
    t0 = time.time()
    with zipfile.ZipFile(xlsx_path, 'r') as z:
        # 1. Shared Strings
        ss = []
        if 'xl/sharedStrings.xml' in z.namelist():
            for event, elem in ET.iterparse(z.open('xl/sharedStrings.xml'), events=('end',)):
                if elem.tag.endswith('t'):
                    ss.append(elem.text or '')
                    elem.clear()
        print(f"Shared strings parsed ({len(ss):,} strings) in {time.time()-t0:.2f}s")

        # 2. Parse Sheet with Positional Mapping
        t1 = time.time()
        sheet_path = 'xl/worksheets/sheet1.xml'
        context = ET.iterparse(z.open(sheet_path), events=('end',))

        # We will build col_idx_map: column_letter -> field_index
        col_idx_map = {}
        rows = []
        month_counts = {}

        field_names = [
            'delivery_date', 'mtm_type', 'branch', 'mtm_alias', 'brand_group',
            'product_code', 'item_name', 'reason_kirim', 'reason_realisasi',
            'idr_kirim', 'idr_realisasi', 'idr_pesan', 'qty_kirim', 'qty_realisasi', 'qty_order'
        ]

        row_count = 0
        for event, elem in context:
            if elem.tag.endswith('row'):
                r_num = elem.attrib.get('r')
                row_vals = {}

                for cell in elem:
                    if cell.tag.endswith('c'):
                        ref = cell.attrib.get('r', '')
                        col_let = ''.join([ch for ch in ref if ch.isalpha()])
                        t_type = cell.attrib.get('t', '')
                        
                        # Get cell value
                        val = ''
                        for child in cell:
                            if child.tag.endswith('v'):
                                val = child.text or ''
                                break
                        
                        if t_type == 's' and val.isdigit():
                            idx = int(val)
                            val = ss[idx] if idx < len(ss) else val
                        
                        row_vals[col_let] = val

                if r_num == '1':
                    for col_let, val in row_vals.items():
                        hu = str(val).upper().strip()
                        if hu in ['DELIVERY_DATE', 'TGL_NP', 'TGL KIRIM']: col_idx_map[col_let] = 0
                        elif hu in ['JENIS MTM', 'JENIS_MTM']: col_idx_map[col_let] = 1
                        elif hu in ['BRANCH_NAME', 'CABANG']: col_idx_map[col_let] = 2
                        elif hu in ['MTM_ALIAS', 'MTM ALIAS']: col_idx_map[col_let] = 3
                        elif hu in ['GROUP BRAND', 'GRUP BRAND', 'GROUP_BRAND']: col_idx_map[col_let] = 4
                        elif hu in ['PRODUCT_CODE', 'KODE ITEM', 'KODE_ITEM']: col_idx_map[col_let] = 5
                        elif hu in ['PRODUCT_NAME', 'NAMA ITEM', 'ITEM']: col_idx_map[col_let] = 6
                        elif hu in ['ALASAN_TIDAK_TERKIRIM', 'ALASAN KIRIM']: col_idx_map[col_let] = 7
                        elif hu in ['ALASAN_REALISASI']: col_idx_map[col_let] = 8
                        elif hu in ['R_KIRIM', 'NOMINAL KIRIM']: col_idx_map[col_let] = 9
                        elif hu in ['RP_REALISASI', 'NOMINAL REALISASI']: col_idx_map[col_let] = 10
                        elif hu in ['R_PESAN', 'NOMINAL PESAN']: col_idx_map[col_let] = 11
                        elif hu in ['QTY_DELIVERY_IN_SMALLEST_UNIT', 'QTY KIRIM']: col_idx_map[col_let] = 12
                        elif hu in ['QTY_REALISASI']: col_idx_map[col_let] = 13
                        elif hu in ['QTY_ORDER_IN_SMALLEST_UNIT', 'QTY ORDER']: col_idx_map[col_let] = 14
                else:
                    row_count += 1
                    # Extract tuple values directly
                    dt = row_vals.get(next((k for k, v in col_idx_map.items() if v == 0), ''), '').strip()
                    rk = row_vals.get(next((k for k, v in col_idx_map.items() if v == 7), ''), '').strip()
                    rr = row_vals.get(next((k for k, v in col_idx_map.items() if v == 8), ''), '').strip()
                    
                    if rk != "" and rr == "": reason_final = rk
                    elif rk == "" and rr != "": reason_final = rr
                    elif rk != "" and rr != "": reason_final = rk
                    else: reason_final = 'On-Time / Sesuai'

                    if len(dt) >= 10 and '-' in dt: month = dt[:7]
                    elif len(dt) >= 6 and dt[:6].isdigit(): month = f"{dt[:4]}-{dt[4:6]}"
                    elif len(dt) >= 7 and dt[:4].isdigit(): month = dt[:7]
                    else: month = '2026-08'

                    if month:
                        month_counts[month] = month_counts.get(month, 0) + 1

                elem.clear()

        print(f"Parsed {row_count:,} rows in {time.time()-t1:.2f}s. Total time: {time.time()-t0:.2f}s")
        print("Detected months:", month_counts)

if __name__ == "__main__":
    benchmark_positional("uploaded_active_dataset.xlsx")
