import urllib.request
import json
import time
import subprocess
import sys
import os

def test_api():
    base_url = "http://127.0.0.1:5000"

    
    print("1. Testing /api/health...")
    req = urllib.request.Request(f"{base_url}/api/health")
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode())
        print("Health Response:", data)
        assert data["status"] == "ok"
        
    print("\n2. Testing /api/auth/login (Admin)...")
    login_data = json.dumps({"username": "admin", "password": "konimex123"}).encode()
    req = urllib.request.Request(f"{base_url}/api/auth/login", data=login_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode())
        print("Login Admin Response:", data)
        assert data["user"]["role"] == "admin"
        assert data["user"]["can_upload"] == True

    print("\n3. Testing /api/auth/login (Konimex User)...")
    login_user_data = json.dumps({"username": "konimex", "password": "konimex123"}).encode()
    req = urllib.request.Request(f"{base_url}/api/auth/login", data=login_user_data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode())
        print("Login User Response:", data)
        assert data["user"]["role"] == "user"
        assert data["user"]["can_upload"] == False

    print("\n4. Testing /api/data/filters...")
    req = urllib.request.Request(f"{base_url}/api/data/filters")
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode())
        print("Filter Options Keys:", list(data["data"].keys()))
        assert "months" in data["data"]

    print("\n5. Testing /api/analytics/kpi...")
    kpi_payload = json.dumps({"metric_type": "idr"}).encode()
    req = urllib.request.Request(f"{base_url}/api/analytics/kpi", data=kpi_payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode())
        print("KPI Scorecard Response:", data["data"])
        assert "sl_kirim" in data["data"]

    print("\n6. Testing /api/analytics/pareto (Alasan)...")
    pareto_payload = json.dumps({"dimension": "alasan", "metric_type": "idr"}).encode()
    req = urllib.request.Request(f"{base_url}/api/analytics/pareto", data=pareto_payload, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req) as res:
        data = json.loads(res.read().decode())
        print("Pareto Response Dimension:", data["dimension"])
        assert data["status"] == "success"

    print("\n--- ALL BACKEND REST API ENDPOINT TESTS PASSED SUCCESSFULLY! ---")

if __name__ == "__main__":
    test_api()
