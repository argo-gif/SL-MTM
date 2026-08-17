import urllib.request
import json
import sys
import os

def test_filters_and_kpi():
    base_url = "http://127.0.0.1:5000"
    
    print("1. Testing GET /api/data/filters (Cascading Filter Options)...")
    req = urllib.request.Request(f"{base_url}/api/data/filters")
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        data = json.loads(res.read().decode('utf-8'))
        opts = data["data"]
        print("Latest Month:", opts["latest_month"])
        print("Default MTM Type:", opts["default_mtm_type"])
        print("Branches Count:", len(opts["branches"]))
        assert len(opts["months"]) > 0
        assert opts["default_mtm_type"] != ""

    print("\n2. Testing POST /api/analytics/kpi (IDR Metric Toggle)...")
    payload_idr = json.dumps({"metric_type": "idr", "month": opts["latest_month"], "mtm_type": opts["default_mtm_type"]}).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/api/analytics/kpi", data=payload_idr, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        data = json.loads(res.read().decode('utf-8'))
        kpi_idr = data["data"]
        print("KPI Scorecard (IDR):", kpi_idr)
        assert "sl_kirim" in kpi_idr
        assert "sl_realisasi" in kpi_idr
        assert kpi_idr["target"] == 85.0

    print("\n3. Testing POST /api/analytics/kpi (QTY Metric Toggle)...")
    payload_qty = json.dumps({"metric_type": "qty", "month": opts["latest_month"], "mtm_type": opts["default_mtm_type"]}).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/api/analytics/kpi", data=payload_qty, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        data = json.loads(res.read().decode('utf-8'))
        kpi_qty = data["data"]
        print("KPI Scorecard (QTY):", kpi_qty)
        assert kpi_qty["target"] == 85.0

    print("\n--- FILTER CONTROLS & KPI SCORECARDS UNIT TESTS PASSED 100%! ---")

if __name__ == "__main__":
    test_filters_and_kpi()
