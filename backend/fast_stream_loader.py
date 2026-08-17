import zipfile
import xml.etree.ElementTree as ET
import time
import re

def load_dataset_fast(xlsx_path="uploaded_active_dataset.xlsx"):
    start = time.time()
    print(f"Streaming load of {xlsx_path}...")
    
    with zipfile.ZipFile(xlsx_path, 'r') as z:
        # 1. Read shared strings array
        shared_strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            ss_bytes = z.read('xl/sharedStrings.xml')
            # Extract all <t> text using fast regex
            shared_strings = re.findall(r'<t[^>]*>(.*?)</t>', ss_bytes.decode('utf-8', errors='ignore'), re.DOTALL)
            print(f"Extracted {len(shared_strings)} shared strings in {time.time() - start:.2f}s")

        # 2. Stream sheet XML
        sheet_path = 'xl/worksheets/sheet1.xml'
        if sheet_path not in z.namelist():
            for name in z.namelist():
                if name.startswith('xl/worksheets/sheet'):
                    sheet_path = name
                    break

        print("Streaming worksheet rows...")
        sheet_file = z.open(sheet_path)
        
        # We process row by row using ElementTree.iterparse
        context = ET.iterparse(sheet_file, events=('end',))
        
        records = []
        headers = []
        header_map = {}
        
        for event, elem in context:
            if elem.tag.endswith('row'):
                row_vals = []
                for cell in elem:
                    t = cell.attrib.get('t')
                    v_elem = cell.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                    val = v_elem.text if v_elem is not None else ''
                    if t == 's' and val != '' and val.isdigit():
                        idx = int(val)
                        val = shared_strings[idx] if idx < len(shared_strings) else val
                    row_vals.append(val)

                if not headers:
                    headers = [str(h).strip().upper() for h in row_vals]
                    for i, h in enumerate(headers):
                        if 'DELIVERY_DATE' in h or 'TGL' in h: header_map[i] = 'delivery_date'
                        elif 'JENIS MTM' in h or 'JENIS_MTM' in h: header_map[i] = 'mtm_type'
                        elif 'BRANCH_NAME' in h or 'CABANG' in h: header_map[i] = 'branch'
                        elif 'MTM_ALIAS' in h or 'MTM ALIAS' in h: header_map[i] = 'mtm_alias'
                        elif 'GROUP BRAND' in h or 'GRUP BRAND' in h: header_map[i] = 'brand_group'
                        elif 'PRODUCT_NAME' in h or 'NAMA ITEM' in h or 'ITEM' in h: header_map[i] = 'item_name'
                        elif 'ALASAN_TIDAK_TERKIRIM' in h or 'ALASAN KIRIM' in h: header_map[i] = 'reason_kirim'
                        elif 'ALASAN_REALISASI' in h: header_map[i] = 'reason_realisasi'
                        elif 'R_KIRIM' in h: header_map[i] = 'idr_kirim'
                        elif 'RP_REALISASI' in h: header_map[i] = 'idr_realisasi'
                        elif 'R_PESAN' in h: header_map[i] = 'idr_pesan'
                        elif 'QTY_DELIVERY' in h or 'QTY KIRIM' in h: header_map[i] = 'qty_kirim'
                        elif 'QTY_REALISASI' in h: header_map[i] = 'qty_realisasi'
                        elif 'QTY_ORDER' in h: header_map[i] = 'qty_order'
                        else: header_map[i] = h
                else:
                    rec = {}
                    for idx, val in enumerate(row_vals):
                        fname = header_map.get(idx, f"col_{idx}")
                        rec[fname] = val

                    # Reason logic
                    rk = str(rec.get('reason_kirim') or '').strip()
                    rr = str(rec.get('reason_realisasi') or '').strip()
                    if rk != "" and rr == "": rec['reason_final'] = rk
                    elif rk == "" and rr != "": rec['reason_final'] = rr
                    elif rk != "" and rr != "": rec['reason_final'] = rk
                    else: rec['reason_final'] = 'On-Time / Sesuai'

                    # Month
                    dt = str(rec.get('delivery_date') or '')
                    if len(dt) >= 7 and dt[:4].isdigit():
                        rec['month'] = dt[:7]
                    else:
                        rec['month'] = '2026-01'

                    rec['mtm_type'] = str(rec.get('mtm_type') or 'KA')
                    rec['branch'] = str(rec.get('branch') or 'Cabang Main')
                    rec['mtm_alias'] = str(rec.get('mtm_alias') or 'Alias Standard')
                    rec['brand_group'] = str(rec.get('brand_group') or 'Group General')
                    rec['item_name'] = str(rec.get('item_name') or 'Item MTM')

                    try: rec['idr_kirim'] = float(rec.get('idr_kirim') or 0)
                    except: rec['idr_kirim'] = 0.0
                    try: rec['idr_realisasi'] = float(rec.get('idr_realisasi') or 0)
                    except: rec['idr_realisasi'] = 0.0
                    try: rec['qty_kirim'] = float(rec.get('qty_kirim') or 0)
                    except: rec['qty_kirim'] = 0.0
                    try: rec['qty_realisasi'] = float(rec.get('qty_realisasi') or 0)
                    except: rec['qty_realisasi'] = 0.0

                    records.append(rec)

                elem.clear() # Free memory immediately for streamed elements

        print(f"STREAMING LOAD COMPLETED! Total Loaded Records: {len(records)} in {time.time() - start:.2f} seconds.")
        return records

if __name__ == "__main__":
    recs = load_dataset_fast()
    print("Sample record 0:", recs[0] if recs else {})
