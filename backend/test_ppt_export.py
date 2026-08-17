import sys
import os
import urllib.request
import json

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ppt_exporter import MTMPPTExporter
from data_processor import MTMDataProcessor

def test_ppt_generation_direct():
    print("1. Testing MTMPPTExporter direct generation...")
    processor = MTMDataProcessor("uploaded_active_dataset.xlsx")
    processor.load_data()
    
    records = processor.records
    export_data = {
        "kpi": processor.get_kpi_scorecard(records, metric_type="idr"),
        "trend": processor.get_monthly_trend({}, metric_type="idr"),
        "pareto": {
            "alasan": processor.get_pareto_tree_maps(records, "alasan", metric_type="idr"),
            "mtm_alias": processor.get_pareto_tree_maps(records, "mtm_alias", metric_type="idr"),
            "cabang": processor.get_pareto_tree_maps(records, "cabang", metric_type="idr"),
            "grup_brand": processor.get_pareto_tree_maps(records, "grup_brand", metric_type="idr"),
            "item": processor.get_pareto_tree_maps(records, "item", metric_type="idr"),
        },
        "grid": processor.get_detail_grid(records, limit=10),
        "selected_modules": {
            "kpi_summary": True,
            "pareto_sheets": True,
            "detail_grid": True
        }
    }
    
    exporter = MTMPPTExporter("Template PPT.pptx")
    out_file = "test_generated_report.pptx"
    result_path = exporter.generate_presentation(export_data, out_file)
    
    assert os.path.exists(result_path), "Generated PPT file does not exist!"
    file_size = os.path.getsize(result_path)
    print(f"Generated PPT file: {result_path} (Size: {file_size} bytes)")
    assert file_size > 1000, "PPT file is empty or corrupted!"
    print("Direct PPT Generation TEST PASSED!")

def test_ppt_export_endpoint():
    print("\n2. Testing /api/export/ppt REST API endpoint...")
    base_url = "http://127.0.0.1:5000"
    payload = json.dumps({
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
        print(f"API returned PPT binary file. Length: {len(data_bytes)} bytes")
        assert len(data_bytes) > 1000, "API returned empty PPT payload!"
        
        with open("downloaded_api_test.pptx", "wb") as f:
            f.write(data_bytes)
        print("API PPT Export Endpoint TEST PASSED!")

if __name__ == "__main__":
    test_ppt_generation_direct()
    test_ppt_export_endpoint()
