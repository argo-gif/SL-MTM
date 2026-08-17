import zipfile
import xml.etree.ElementTree as ET
import re

def inspect_xlsx(path):
    with zipfile.ZipFile(path, 'r') as z:
        # Get shared strings
        shared_strings = []
        if 'xl/sharedStrings.xml' in z.namelist():
            ss_tree = ET.fromstring(z.read('xl/sharedStrings.xml'))
            for elem in ss_tree.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}t'):
                shared_strings.append(elem.text or '')
                
        # Get sheet 1
        sheet_path = 'xl/worksheets/sheet1.xml'
        if sheet_path not in z.namelist():
            # find first sheet
            for name in z.namelist():
                if name.startswith('xl/worksheets/sheet'):
                    sheet_path = name
                    break
                    
        print("Reading sheet:", sheet_path)
        sheet_tree = ET.fromstring(z.read(sheet_path))
        
        rows = []
        for row in sheet_tree.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}row'):
            row_vals = []
            for cell in row.iter('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}c'):
                t = cell.attrib.get('t')
                v_elem = cell.find('{http://schemas.openxmlformats.org/spreadsheetml/2006/main}v')
                val = v_elem.text if v_elem is not None else None
                if t == 's' and val is not None:
                    val = shared_strings[int(val)]
                row_vals.append(val)
            rows.append(row_vals)
            if len(rows) >= 5:
                break
                
        print("\nHeader (Row 1):")
        print(rows[0] if rows else [])
        print("\nRow 2 Sample:")
        print(rows[1] if len(rows) > 1 else [])

if __name__ == "__main__":
    inspect_xlsx("uploaded_active_dataset.xlsx")
