import urllib.request
import json
import sys
import os

def test_grid_and_export():
    base_url = "http://127.0.0.1:5000"
    
    print("1. Testing POST /api/analytics/grid (Data Grid Sync)...")
    payload_grid = json.dumps({"month": "2026-01", "mtm_type": "KA", "limit": 100}).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/api/analytics/grid", data=payload_grid, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        data = json.loads(res.read().decode('utf-8'))
        records = data["data"]
        print("Data Grid Records Count:", len(records))
        assert len(records) > 0
        r0 = records[0]
        assert "month" in r0
        assert "branch" in r0
        assert "brand_group" in r0
        assert "item_name" in r0
        assert "idr_kirim" in r0
        assert "reason_final" in r0
        print("Sample Record:", r0)

    print("\n2. Testing POST /api/export/ppt (PPT Export Modal Integration)...")
    payload_export = json.dumps({
        "month": "2026-01",
        "mtm_type": "KA",
        "selected_modules": {
            "kpi_summary": True,
            "pareto_sheets": True,
            "detail_grid": True
        }
    }).encode('utf-8')
    
    req = urllib.request.Request(f"{base_url}/api/export/ppt", data=payload_export, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        content_type = res.headers.get("Content-Type")
        print("Export Content-Type:", content_type)
        assert "presentation" in content_type or "octet-stream" in content_type
        
        file_bytes = res.read()
        print("Downloaded PPT File Size:", len(file_bytes), "bytes")
        assert len(file_bytes) > 1000

    print("\n--- DATA GRID & PPT EXPORT MODAL UNIT TESTS PASSED 100%! ---")

if __name__ == "__main__":
    test_grid_and_export()
