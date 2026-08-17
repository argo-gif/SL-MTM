import zipfile
import xml.etree.ElementTree as ET
import time

def parse_sheet_fast():
    start = time.time()
    with zipfile.ZipFile("uploaded_active_dataset.xlsx", 'r') as z:
        print("Opening xl/worksheets/sheet1.xml...")
        sheet_file = z.open('xl/worksheets/sheet1.xml')
        row_count = 0
        for event, elem in ET.iterparse(sheet_file, events=('end',)):
            if elem.tag.endswith('row'):
                row_count += 1
                elem.clear()
        print(f"Total Rows: {row_count} loaded in {time.time() - start:.2f}s")

if __name__ == "__main__":
    parse_sheet_fast()
