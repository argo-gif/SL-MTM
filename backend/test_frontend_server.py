import urllib.request

def test_frontend_routes():
    base_url = "http://127.0.0.1:5000"
    
    print("1. Testing index.html route...")
    req = urllib.request.Request(f"{base_url}/")
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        html = res.read().decode('utf-8')
        assert "Dashboard Pemenuhan Service Level MTM" in html
        print("HTML Served Successfully!")

    print("2. Testing src/styles.css route...")
    req = urllib.request.Request(f"{base_url}/src/styles.css")
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        css = res.read().decode('utf-8')
        assert "--konimex-red" in css
        print("CSS Served Successfully!")

    print("3. Testing src/app.js route...")
    req = urllib.request.Request(f"{base_url}/src/app.js")
    with urllib.request.urlopen(req) as res:
        assert res.status == 200
        js = res.read().decode('utf-8')
        assert "DashboardApp" in js
        print("JS ES Module Served Successfully!")

    print("\n--- FRONTEND LAYOUT & THEME SERVER TESTS PASSED 100%! ---")

if __name__ == "__main__":
    test_frontend_routes()
