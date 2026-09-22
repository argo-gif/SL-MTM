import os
import sys
from typing import Dict, List, Any
from PIL import Image, ImageDraw, ImageFont

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(__file__))

from ppt_exporter import squarify_layout, generate_treemap_image

if __name__ == "__main__":
    sample_items = [
        {"name": "STOCK OUT PRINCIPAL", "value": 1080000000, "percentage": 43.2, "cumulative_percentage": 43.2},
        {"name": "STOCK OUT CABANG", "value": 533200000, "percentage": 21.4, "cumulative_percentage": 64.6},
        {"name": "PO SALAH HARGA/DISC", "value": 297960000, "percentage": 11.9, "cumulative_percentage": 76.5},
        {"name": "BARANG DALAM PERJALANAN (BDP)", "value": 274410000, "percentage": 11.0, "cumulative_percentage": 87.5},
        {"name": "PRODUK SUDAH TIDAK PRODUKSI", "value": 147060000, "percentage": 5.9, "cumulative_percentage": 93.4},
        {"name": "PELANGGAN TIDAK BERIZIN", "value": 134380000, "percentage": 5.4, "cumulative_percentage": 98.8},
        {"name": "DIASWEET FIBERWAFER CHOCOLATE 18 G", "value": 35610000, "percentage": 1.4, "cumulative_percentage": 100.0},
        {"name": "TERMOREX PLUS 60 ML", "value": 20000000, "percentage": 0.8, "cumulative_percentage": 100.0},
        {"name": "GET GIT WAFER 100 G", "value": 20000000, "percentage": 0.8, "cumulative_percentage": 100.0},
        {"name": "BRINGZ LUMIER CHOCOLATE", "value": 17500000, "percentage": 0.7, "cumulative_percentage": 100.0},
        {"name": "BRAITO ORIGINAL 5 ML", "value": 15000000, "percentage": 0.6, "cumulative_percentage": 100.0},
    ]
    out_file = generate_treemap_image(sample_items, vital_cutoff_idx=3)
    print(f"Generated test treemap image: {out_file}")
