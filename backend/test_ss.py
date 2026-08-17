import zipfile
import xml.etree.ElementTree as ET
import time

def parse_ss():
    start = time.time()
    with zipfile.ZipFile("uploaded_active_dataset.xlsx", 'r') as z:
        print("Opening sharedStrings.xml...")
        ss_file = z.open('xl/sharedStrings.xml')
        strings = []
        for event, elem in ET.iterparse(ss_file, events=('end',)):
            if elem.tag.endswith('t'):
                strings.append(elem.text or '')
                elem.clear()
        print(f"Total Shared Strings: {len(strings)} loaded in {time.time() - start:.2f}s")
        return strings

if __name__ == "__main__":
    parse_ss()
