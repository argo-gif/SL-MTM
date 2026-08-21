import sys
sys.stdout.reconfigure(encoding='utf-8')
from backend.data_processor import MTMDataProcessor

proc = MTMDataProcessor('backend/dataset.db')
filters = {'month': '2026-08', 'mtm_type': 'KA'}
gb_grid = proc.get_detail_grid(filters, dimension='grup_brand', limit=200)

print(f"Total Grup Brand found: {len(gb_grid)}")
for i, gb in enumerate(gb_grid):
    name = gb.get('name')
    sl_k = float(gb.get('sl_kirim', 0))
    sl_r = float(gb.get('sl_realisasi', 0))
    gap = sl_r - sl_k
    val = float(gb.get('gap_unfulfill', 0))
    tp = float(gb.get('total_pesan', gb.get('total_p', 0)))
    tk = float(gb.get('total_kirim', gb.get('total_k', 0)))
    tr = float(gb.get('total_realisasi', gb.get('total_r', 0)))
    print(f"GB #{i+1}: {name} | Order: Rp {tp:,.0f} | Kirim: Rp {tk:,.0f} ({sl_k:.1f}%) | Realisasi: Rp {tr:,.0f} ({sl_r:.1f}%) | GAP: {gap:+.1f}% | Unfulfill: Rp {val:,.0f}")
