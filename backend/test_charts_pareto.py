import urllib.request
import json
import sys
import os

def test_charts_and_pareto():
    base_url = "http://127.0.0.1:5000"
    
    print("1. Testing POST /api/analytics/trend (Monthly Trend)...")
    payload_trend = json.dumps({"metric_type": "idr", "mtm_type": "KA"}).encode('utf-8')
    req = urllib.request.Request(f"{base_url}/api/analytics/trend", data=payload_trend, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        data = json.loads(res.read().decode('utf-8'))
        trend = data["data"]
        print("Monthly Trend Items:", len(trend))
        assert len(trend) > 0
        assert "sl_kirim" in trend[0]
        assert "sl_realisasi" in trend[0]

    dims = ["alasan", "mtm_alias", "cabang", "grup_brand", "item"]
    for dim in dims:
        print(f"\n2. Testing POST /api/analytics/pareto (Dimension: {dim})...")
        payload_p = json.dumps({"dimension": dim, "metric_type": "idr", "mtm_type": "KA"}).encode('utf-8')
        req = urllib.request.Request(f"{base_url}/api/analytics/pareto", data=payload_p, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as res:
            assert res.status == 200
            data = json.loads(res.read().decode('utf-8'))
            items = data["data"]
            print(f"Pareto {dim} items count: {len(items)}")
            if items:
                print(f" Top Item: {items[0]['name']} (Contrib: {items[0]['percentage']}%, Cumulative: {items[0]['cumulative_percentage']}%)")
                assert "name" in items[0]
                assert "value" in items[0]
                assert "cumulative_percentage" in items[0]

    print("\n--- ANALYTICS CHARTS & PARETO TREE MAPS UNIT TESTS PASSED 100%! ---")

if __name__ == "__main__":
    test_charts_and_pareto()
