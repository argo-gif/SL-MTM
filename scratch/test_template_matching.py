import sys
sys.stdout.reconfigure(encoding='utf-8')
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from backend.data_processor import MTMDataProcessor
from backend.ppt_exporter import MTMPPTExporter

proc = MTMDataProcessor('backend/dataset.db')
filters = {'month': '2026-08', 'mtm_type': 'KA'}
data = {
    'filters': filters,
    'kpi': proc.get_kpi_scorecard(filters),
    'trend': proc.get_monthly_trend(filters),
    'pareto': {
        'alasan': proc.get_pareto_tree_maps(filters, dimension='alasan'),
        'mtm_alias': proc.get_pareto_tree_maps(filters, dimension='mtm_alias'),
        'cabang': proc.get_pareto_tree_maps(filters, dimension='cabang'),
        'grup_brand': proc.get_pareto_tree_maps(filters, dimension='grup_brand'),
        'item': proc.get_pareto_tree_maps(filters, dimension='item')
    },
    'grid_by_dim': {
        'alasan': proc.get_detail_grid(filters, dimension='alasan', limit=200),
        'mtm_alias': proc.get_detail_grid(filters, dimension='mtm_alias', limit=200),
        'cabang': proc.get_detail_grid(filters, dimension='cabang', limit=200),
        'grup_brand': proc.get_detail_grid(filters, dimension='grup_brand', limit=200),
        'item': proc.get_detail_grid(filters, dimension='item', limit=200)
    },
    'selected_modules': {'kpi_summary': True, 'pareto_sheets': True, 'detail_grid': True}
}

exp = MTMPPTExporter()
# We will inspect how layout 2 matches layout of Slide 1
prs = Presentation(exp.template_path)
print("Slide layout 2 name:", prs.slide_layouts[2].name)
print("Slide layout 2 shapes count:", len(prs.slide_layouts[2].shapes))
