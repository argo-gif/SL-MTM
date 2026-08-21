import sys
sys.stdout.reconfigure(encoding='utf-8')
from pptx import Presentation
from backend.data_processor import MTMDataProcessor
from backend.ppt_exporter import MTMPPTExporter, is_all_grup_brand_selected

proc = MTMDataProcessor('backend/dataset.db')
exp = MTMPPTExporter()

# Test case: Specific Grup Brand selected ('GB 1')
f = {'month': '2026-08', 'mtm_type': 'KA', 'grup_brand': 'GB 1'}
data = {
    'filters': f,
    'kpi': proc.get_kpi_scorecard(f),
    'trend': proc.get_monthly_trend(f),
    'pareto': {
        'alasan': proc.get_pareto_tree_maps(f, dimension='alasan'),
        'grup_brand': proc.get_pareto_tree_maps(f, dimension='grup_brand')
    },
    'grid_by_dim': {
        'alasan': proc.get_detail_grid(f, dimension='alasan', limit=200),
        'grup_brand': proc.get_detail_grid(f, dimension='grup_brand', limit=200)
    },
    'selected_modules': {'kpi_summary': True, 'pareto_sheets': True, 'detail_grid': True}
}

print(f"is_all_grup_brand_selected for {f}: {is_all_grup_brand_selected(f)}")
