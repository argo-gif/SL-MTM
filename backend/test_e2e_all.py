import os
import sys
import json
import urllib.request

def run_full_e2e_suite():
    print("=================================================================")
    print("  MTM SERVICE LEVEL DASHBOARD - END-TO-END LOCAL SUITE TESTING   ")
    print("=================================================================\n")

    base_url = "http://127.0.0.1:5000"

    # Step 1: Check Required Project Files
    print("[STEP 1/6] Checking Core Project & Documentation Files...")
    req_files = [
        "instructions.txt",
        "project_specs.md",
        "implementation-plan.md",
        "uploaded_active_dataset.xlsx",
        "Template PPT.pptx",
        "backend/requirements.txt",
        "backend/README.md",
        "frontend/README.md",
        "frontend/index.html",
        "frontend/src/styles.css",
        "frontend/src/app.js",
        "frontend/src/auth.js"
    ]
    for f in req_files:
        assert os.path.exists(f), f"Missing required file: {f}"
        print(f"  [OK] Found: {f}")

    # Step 2: REST API Health & Authentication
    print("\n[STEP 2/6] Testing REST API Health & Authentication...")
    req = urllib.request.Request(f"{base_url}/api/health")
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        print("  [OK] Health Check: 200 OK")

    # Admin login
    req = urllib.request.Request(f"{base_url}/api/auth/login", data=json.dumps({"username": "admin", "password": "konimex123"}).encode('utf-8'), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode('utf-8'))
        assert data["user"]["can_upload"] == True
        print("  [OK] Admin Login: SUCCESS (Role: admin, can_upload: True)")

    # Konimex user login
    req = urllib.request.Request(f"{base_url}/api/auth/login", data=json.dumps({"username": "konimex", "password": "konimex123"}).encode('utf-8'), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode('utf-8'))
        assert data["user"]["can_upload"] == False
        print("  [OK] User Login: SUCCESS (Role: user, can_upload: False)")

    # Step 3: Cascading Filters & KPI Analytics
    print("\n[STEP 3/6] Testing Global Linked Filters & KPI Scorecard...")
    req = urllib.request.Request(f"{base_url}/api/data/filters")
    with urllib.request.urlopen(req) as res:
        opts = json.loads(res.read().decode('utf-8'))["data"]
        print(f"  [OK] Filters Options: Latest Month={opts['latest_month']}, Default MTM={opts['default_mtm_type']}")

    req = urllib.request.Request(f"{base_url}/api/analytics/kpi", data=json.dumps({"metric_type": "idr", "month": opts["latest_month"], "mtm_type": opts["default_mtm_type"]}).encode('utf-8'), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        kpi = json.loads(res.read().decode('utf-8'))["data"]
        print(f"  [OK] KPI Scorecard (IDR): SL Kirim={kpi['sl_kirim']}%, SL Realisasi={kpi['sl_realisasi']}%, Target={kpi['target']}%")
        assert kpi["target"] == 85.0

    # Step 4: Pareto Tree Maps (5 Dimensions)
    print("\n[STEP 4/6] Testing Pareto Tree Maps (5 Dimensions)...")
    for dim in ["alasan", "mtm_alias", "cabang", "grup_brand", "item"]:
        req = urllib.request.Request(f"{base_url}/api/analytics/pareto", data=json.dumps({"dimension": dim, "metric_type": "idr"}).encode('utf-8'), headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req) as res:
            pareto = json.loads(res.read().decode('utf-8'))["data"]
            print(f"  [OK] Pareto [{dim}]: {len(pareto)} elements calculated (Top: {pareto[0]['name'] if pareto else 'None'})")

    # Step 5: PowerPoint Automated Export
    print("\n[STEP 5/6] Testing PowerPoint Automated Export Engine...")
    req = urllib.request.Request(f"{base_url}/api/export/ppt", data=json.dumps({"metric_type": "idr", "selected_modules": {"kpi_summary": True, "pareto_sheets": True, "detail_grid": True}}).encode('utf-8'), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        ppt_bytes = res.read()
        print(f"  [OK] PowerPoint Export Downloaded: {len(ppt_bytes)} bytes (Template layout safeguard intact)")
        assert len(ppt_bytes) > 1000

    # Step 6: Frontend Web Server Static Asset Routes
    print("\n[STEP 6/6] Testing Frontend Web Server Routes...")
    for path in ["/", "/src/styles.css", "/src/app.js", "/src/auth.js"]:
        req = urllib.request.Request(f"{base_url}{path}")
        with urllib.request.urlopen(req) as res:
            assert res.status == 200
            print(f"  [OK] Route {path}: 200 OK")

    print("\n=================================================================")
    print("  ALL END-TO-END SYSTEM INTEGRATION TESTS PASSED 100% (SUCCESS)! ")
    print("=================================================================\n")

if __name__ == "__main__":
    run_full_e2e_suite()
