import sys
import os
import urllib.request
import json

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ppt_exporter import MTMPPTExporter
from data_processor import MTMDataProcessor

def test_ppt_generation_direct():
    print("1. Testing MTMPPTExporter direct generation (Single & Multi-Month)...")
    processor = MTMDataProcessor()
    
    # Test multi-month export payload (July & August 2026)
    months = ["2026-07", "2026-08"]
    period_reports = []
    for m in months:
        m_filters = {"month": m, "mtm_type": "KA"}
        rep = {
            "filters": m_filters,
            "kpi": processor.get_kpi_scorecard(m_filters, metric_type="idr"),
            "trend": processor.get_monthly_trend(m_filters, metric_type="idr"),
            "pareto": {
                "alasan": processor.get_pareto_tree_maps(m_filters, dimension="alasan", metric_type="idr"),
                "mtm_alias": processor.get_pareto_tree_maps(m_filters, dimension="mtm_alias", metric_type="idr"),
                "cabang": processor.get_pareto_tree_maps(m_filters, dimension="cabang", metric_type="idr"),
                "grup_brand": processor.get_pareto_tree_maps(m_filters, dimension="grup_brand", metric_type="idr"),
                "item": processor.get_pareto_tree_maps(m_filters, dimension="item", metric_type="idr"),
            },
            "grid_by_dim": {
                "alasan": processor.get_detail_grid(m_filters, dimension="alasan", metric_type="idr", limit=200),
                "mtm_alias": processor.get_detail_grid(m_filters, dimension="mtm_alias", metric_type="idr", limit=200),
                "cabang": processor.get_detail_grid(m_filters, dimension="cabang", metric_type="idr", limit=200),
                "grup_brand": processor.get_detail_grid(m_filters, dimension="grup_brand", metric_type="idr", limit=200),
                "item": processor.get_detail_grid(m_filters, dimension="item", metric_type="idr", limit=200),
            },
            "grid": processor.get_detail_grid(m_filters, limit=50),
            "selected_modules": {"kpi_summary": True, "pareto_sheets": True, "detail_grid": True}
        }
        period_reports.append(rep)

    export_data = {
        "filters": {"months": months, "mtm_type": "KA"},
        "period_reports": period_reports,
        "selected_modules": {"kpi_summary": True, "pareto_sheets": True, "detail_grid": True}
    }
    
    exporter = MTMPPTExporter("Template PPT.pptx")
    out_file = "test_generated_report.pptx"
    result_path = exporter.generate_presentation(export_data, out_file)
    
    assert os.path.exists(result_path), "Generated PPT file does not exist!"
    file_size = os.path.getsize(result_path)
    print(f"Generated Multi-Month PPT file: {result_path} (Size: {file_size} bytes)")
    assert file_size > 1000, "PPT file is empty or corrupted!"
    print("Direct Multi-Month PPT Generation TEST PASSED!")

def test_ppt_export_endpoint():
    print("\n2. Testing /api/export/ppt REST API endpoint (Multi-Month)...")
    base_url = "http://127.0.0.1:5000"
    payload = json.dumps({
        "months": ["2026-07", "2026-08"],
        "metric_type": "idr",
        "selected_modules": {
            "kpi_summary": True,
            "pareto_sheets": True,
            "detail_grid": True
        }
    }).encode('utf-8')
    
    req = urllib.request.Request(f"{base_url}/api/export/ppt", data=payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        assert res.status == 200, f"Expected 200 OK, got {res.status}"
        data_bytes = res.read()
        print(f"API returned Multi-Month PPT binary file. Length: {len(data_bytes)} bytes")
        assert len(data_bytes) > 1000, "API returned empty PPT payload!"
        
        with open("downloaded_api_test.pptx", "wb") as f:
            f.write(data_bytes)
        print("API Multi-Month PPT Export Endpoint TEST PASSED!")

if __name__ == "__main__":
    test_ppt_generation_direct()
    try:
        test_ppt_export_endpoint()
    except Exception as e:
        print(f"Notice for API endpoint test: {e} (Backend server may not be running locally)")
