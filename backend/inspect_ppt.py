import zipfile
import xml.etree.ElementTree as ET
import sys
import os

def inspect_pptx(path="Template PPT.pptx"):
    if not os.path.exists(path):
        print(f"PPT template not found at {path}")
        return
        
    print(f"Inspecting {path}...")
    with zipfile.ZipFile(path, 'r') as z:
        namelist = z.namelist()
        print("PPT Structure Files count:", len(namelist))
        
        # Check presentation.xml for slide dimensions
        if 'ppt/presentation.xml' in namelist:
            p_tree = ET.fromstring(z.read('ppt/presentation.xml'))
            sld_sz = p_tree.find('{http://schemas.openxmlformats.org/presentationml/2006/main}sldSz')
            if sld_sz is not None:
                cx = int(sld_sz.attrib.get('cx', 0))
                cy = int(sld_sz.attrib.get('cy', 0))
                print(f"Slide Dimensions: cx={cx} ({cx/914400:.2f} inches), cy={cy} ({cy/914400:.2f} inches)")
                
        # List slides
        slides = [f for f in namelist if f.startswith('ppt/slides/slide') and f.endswith('.xml')]
        print(f"Total Template Slides: {len(slides)}")

if __name__ == "__main__":
    inspect_pptx()
