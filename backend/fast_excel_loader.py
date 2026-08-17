import zipfile
import xml.etree.ElementTree as ET
import time

def parse_full_dataset(xlsx_path="uploaded_active_dataset.xlsx"):
    start = time.time()
    print(f"Loading full dataset from {xlsx_path}...")
    
    with zipfile.ZipFile(xlsx_path, 'r') as z:
        # 1. Parse Shared Strings
        shared_strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            print("Reading shared strings...")
            ss_data = z.read('xl/sharedStrings.xml')
            ss_tree = ET.fromstring(ss_data)
            for elem in ss_tree.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
                shared_strings.append(elem.text or '')
            print(f"Loaded {len(shared_strings)} shared strings.")
            
        # 2. Parse Sheet1
        sheet_path = 'xl/worksheets/sheet1.xml'
        if sheet_path not in z.namelist():
            for name in z.namelist():
                if name.startswith('xl/worksheets/sheet'):
                    sheet_path = name
                    break
                    
        print(f"Parsing sheet XML ({sheet_path})...")
        sheet_bytes = z.read(sheet_path)
        sheet_tree = ET.fromstring(sheet_bytes)
        
        rows = []
        for row in sheet_tree.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
            row_vals = []
            for cell in row.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                t = cell.attrib.get('t')
                v_elem = cell.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                val = v_elem.text if v_elem is not None else ''
                if t == 's' and val != '' and val.isdigit():
                    idx = int(val)
                    val = shared_strings[idx] if idx < len(shared_strings) else val
                row_vals.append(val)
            rows.append(row_vals)
            
        print(f"Parsed {len(rows)} raw rows in {time.time() - start:.2f}s")
        return rows

if __name__ == "__main__":
    rows = parse_full_dataset()
    print("Header:", rows[0] if rows else [])
    print("Total Rows:", len(rows))
