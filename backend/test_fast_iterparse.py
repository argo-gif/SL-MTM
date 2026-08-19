import time
import zipfile
import xml.etree.ElementTree as ET

def benchmark_iterparse(xlsx_path):
    t0 = time.time()
    with zipfile.ZipFile(xlsx_path, 'r') as z:
        # 1. Shared strings
        ss = []
        if 'xl/sharedStrings.xml' in z.namelist():
            for event, elem in ET.iterparse(z.open('xl/sharedStrings.xml'), events=('end',)):
                if elem.tag.endswith('t'):
                    ss.append(elem.text or '')
                    elem.clear()
        print(f"Shared strings ({len(ss):,} strings) in {time.time()-t0:.2f}s")

        # 2. Sheet rows without XPath find()
        t1 = time.time()
        sheet_path = 'xl/worksheets/sheet1.xml'
        context = ET.iterparse(z.open(sheet_path), events=('end',))
        
        row_count = 0
        for event, elem in context:
            if elem.tag.endswith('row'):
                row_count += 1
                row_cells = {}
                for cell in elem:
                    if cell.tag.endswith('c'):
                        cell_ref = cell.attrib.get('r', '')
                        col_let = ''.join([ch for ch in cell_ref if ch.isalpha()])
                        t_type = cell.attrib.get('t', '')
                        
                        val = ''
                        for child in cell:
                            if child.tag.endswith('v'):
                                val = child.text or ''
                                break
                        
                        if t_type == 's' and val.isdigit():
                            idx = int(val)
                            val = ss[idx] if idx < len(ss) else val
                        
                        row_cells[col_let] = val

                elem.clear()

        print(f"Parsed {row_count:,} rows in {time.time()-t1:.2f}s. Total: {time.time()-t0:.2f}s")

if __name__ == "__main__":
    benchmark_iterparse("uploaded_active_dataset.xlsx")
