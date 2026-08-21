import sys
sys.stdout.reconfigure(encoding='utf-8')
from backend.data_processor import MTMDataProcessor

proc = MTMDataProcessor('backend/dataset.db')
filters = {'month': '2026-08', 'mtm_type': 'KA'}

dims = [
    ('alasan', 'Alasan Keterlambatan'),
    ('mtm_alias', 'Akun MTM Alias'),
    ('cabang', 'Nama Cabang'),
    ('grup_brand', 'Grup Brand'),
    ('item', 'Item SKU')
]

for dim, dim_label in dims:
    pareto_items = proc.get_pareto_tree_maps(filters, dimension=dim)
    vital_items = []
    for item in pareto_items:
        prev_cum = item['cumulative_percentage'] - item['percentage']
        if prev_cum < 80.0:
            vital_items.append(item)
    vital_names = set([v['name'] for v in vital_items])
    
    grid_all = proc.get_detail_grid(filters, dimension=dim, limit=500)
    grid_vital = [g for g in grid_all if g['name'] in vital_names]
    
    print(f'=== Dimensi: {dim_label} ({dim}) ===')
    print(f'  Total Pareto Items: {len(pareto_items)}, Vital Items (<=80%): {len(vital_items)}')
    for v in vital_items:
        print(f'    - {v["name"]}: Rp {v["value"]:,.0f} ({v["percentage"]:.1f}%, Cum: {v["cumulative_percentage"]:.1f}%)')
    print(f'  Detail Grid Vital Rows: {len(grid_vital)}')
