import zipfile
import xml.etree.ElementTree as ET
import time

def count_rows_fast(path="uploaded_active_dataset.xlsx"):
    start = time.time()
    print(f"Reading {path} to count exact rows...")
    with zipfile.ZipFile(path, 'r') as z:
        # Find sheet 1
        sheet_path = 'xl/worksheets/sheet1.xml'
        if sheet_path not in z.namelist():
            for name in z.namelist():
                if name.startswith('xl/worksheets/sheet'):
                    sheet_path = name
                    break
                    
        print("Parsing XML sheet:", sheet_path)
        sheet_data = z.read(sheet_path)
        row_count = sheet_data.count(b'<row ')
        if row_count == 0:
            row_count = sheet_data.count(b'</row>')
            
        print(f"Total Rows in Excel File: {row_count - 1} (Data Rows, excluding header)")
        print(f"Elapsed Time: {time.time() - start:.2f} seconds")
        return row_count

if __name__ == "__main__":
    count_rows_fast()
