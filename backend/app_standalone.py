import os
import sys
import json
import traceback
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import parse_qs, urlparse

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from data_processor import MTMDataProcessor

processor = MTMDataProcessor()
try:
    processor.load_data()
    print("Standalone Server: Database initialized successfully.")
except Exception as e:
    print(f"Standalone Server Warning: Could not load dataset ({e})")


class MTMAPIHandler(BaseHTTPRequestHandler):
    def _send_cors_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, X-User-Role, Authorization')

    def do_OPTIONS(self):
        self.send_response(200)
        self._send_cors_headers()
        self.end_headers()

    def _send_json(self, data, status_code=200):
        self.send_response(status_code)
        self._send_cors_headers()
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            
            if path == '/api/health':
                self._send_json({"status": "ok", "service": "SL MTM Analytics Backend (Standalone)"})
            elif path == '/api/data/filters':
                options = processor.get_filter_options()
                self._send_json({"status": "success", "data": options})
            else:
                clean_p = path.lstrip('/')
                file_target = 'frontend/index.html' if path in ['/', '/index.html'] else os.path.join('frontend', clean_p)
                if not os.path.exists(file_target):
                    file_target = clean_p
                
                if os.path.exists(file_target) and os.path.isfile(file_target):
                    content_type = 'text/html'
                    if file_target.endswith('.css'): content_type = 'text/css'
                    elif file_target.endswith('.js'): content_type = 'application/javascript'
                    elif file_target.endswith('.jpeg') or file_target.endswith('.jpg'): content_type = 'image/jpeg'
                    elif file_target.endswith('.png'): content_type = 'image/png'
                    with open(file_target, 'rb') as f:
                        content_bytes = f.read()
                    self.send_response(200)
                    self._send_cors_headers()
                    self.send_header('Content-Type', content_type)
                    self.send_header('Content-Length', str(len(content_bytes)))
                    self.end_headers()
                    self.wfile.write(content_bytes)
                else:
                    self._send_json({"status": "error", "message": "File or endpoint not found"}, 404)
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            pass
        except Exception as e:
            sys.stderr.write(f"\n--- SERVER ERROR IN GET {self.path} ---\n{traceback.format_exc()}\n")
            sys.stderr.flush()
            try:
                self._send_json({"status": "error", "message": str(e)}, 500)
            except Exception:
                pass


    def do_POST(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            
            content_len = int(self.headers.get('Content-Length', 0))
            body = self.rfile.read(content_len) if content_len > 0 else b'{}'
            try:
                req_data = json.loads(body.decode('utf-8'))
            except Exception:
                req_data = {}

            if path == '/api/auth/login':
                username = str(req_data.get("username", "")).strip().lower()
                password = str(req_data.get("password", "")).strip()

                if username and password == "konimex123":
                    role = "admin" if username == "admin" else "user"
                    self._send_json({
                        "status": "success",
                        "user": {
                            "username": username,
                            "role": role,
                            "can_upload": (role == "admin")
                        },
                        "token": f"token_{username}_12345"
                    })
                else:
                    self._send_json({"status": "error", "message": "Username atau password salah! (Gunakan password: konimex123)"}, 401)


            elif path == '/api/analytics/kpi':
                metric_type = req_data.get("metric_type", "idr")
                scorecard = processor.get_kpi_scorecard(req_data, metric_type=metric_type)
                self._send_json({"status": "success", "data": scorecard})

            elif path == '/api/analytics/trend':
                metric_type = req_data.get("metric_type", "idr")
                trend_data = processor.get_monthly_trend(req_data, metric_type=metric_type)
                self._send_json({"status": "success", "data": trend_data})

            elif path == '/api/analytics/pareto':
                metric_type = req_data.get("metric_type", "idr")
                dimension = req_data.get("dimension", "alasan")
                unfulfill_only = req_data.get("unfulfill_only", True)
                pareto_data = processor.get_pareto_tree_maps(req_data, dimension=dimension, metric_type=metric_type, unfulfill_only=unfulfill_only)
                self._send_json({"status": "success", "data": pareto_data})


            elif path == '/api/analytics/grid':
                limit = int(req_data.get("limit", 500))
                dimension = req_data.get("dimension", "alasan")
                metric_type = req_data.get("metric_type", "idr")
                grid_data = processor.get_detail_grid(req_data, dimension=dimension, metric_type=metric_type, limit=limit)
                self._send_json({"status": "success", "data": grid_data})


            elif path == '/api/data/upload':
                try:
                    content_length = int(self.headers.get('Content-Length', 0))
                    file_bytes = self.rfile.read(content_length)
                    
                    if not file_bytes:
                        self._send_json({"status": "error", "message": "File payload kosong"}, 400)
                        return
                    
                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    target_xlsx = os.path.join(base_dir, "uploaded_active_dataset.xlsx")
                    target_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset.db")
                    
                    with open(target_xlsx, 'wb') as f:
                        f.write(file_bytes)
                        
                    if os.path.exists(target_db):
                        try: os.remove(target_db)
                        except: pass
                        
                    from build_dataset_db_v2 import build_db
                    build_db(xlsx_path=target_xlsx, db_path=target_db)
                    
                    self._send_json({"status": "success", "message": "Dataset Excel berhasil diunggah dan database terindeks ulang."})
                except Exception as ex:
                    traceback.print_exc()
                    self._send_json({"status": "error", "message": f"Gagal memproses upload: {str(ex)}"}, 500)

            elif path == '/api/export/ppt':

                try:
                    from ppt_exporter import MTMPPTExporter
                    exporter = MTMPPTExporter()
                    metric_type = req_data.get("metric_type", "idr")
                    export_data = {
                        "kpi": processor.get_kpi_scorecard(req_data, metric_type=metric_type),
                        "trend": processor.get_monthly_trend(req_data, metric_type=metric_type),
                        "pareto": {
                            "alasan": processor.get_pareto_tree_maps(req_data, dimension="alasan", metric_type=metric_type),
                            "mtm_alias": processor.get_pareto_tree_maps(req_data, dimension="mtm_alias", metric_type=metric_type),
                            "cabang": processor.get_pareto_tree_maps(req_data, dimension="cabang", metric_type=metric_type),
                            "grup_brand": processor.get_pareto_tree_maps(req_data, dimension="grup_brand", metric_type=metric_type),
                            "item": processor.get_pareto_tree_maps(req_data, dimension="item", metric_type=metric_type),
                        },
                        "grid": processor.get_detail_grid(req_data, limit=50),
                        "selected_modules": req_data.get("selected_modules", {"kpi_summary": True, "pareto_sheets": True, "detail_grid": True})
                    }
                    output_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "generated_mtm_report.pptx")
                    exporter.generate_presentation(export_data, output_file)
                    
                    if os.path.exists(output_file):
                        with open(output_file, 'rb') as f:
                            ppt_bytes = f.read()
                        self.send_response(200)
                        self._send_cors_headers()
                        self.send_header('Content-Type', 'application/vnd.openxmlformats-officedocument.presentationml.presentation')
                        self.send_header('Content-Disposition', 'attachment; filename="Laporan_Service_Level_MTM.pptx"')
                        self.send_header('Content-Length', str(len(ppt_bytes)))
                        self.end_headers()
                        self.wfile.write(ppt_bytes)
                    else:
                        self._send_json({"status": "error", "message": "Gagal membuat file presentasi PPT"}, 500)
                except Exception as ex:
                    traceback.print_exc()
                    self._send_json({"status": "error", "message": f"Gagal mengekspor PPT: {str(ex)}"}, 500)

            else:
                self._send_json({"status": "error", "message": "Endpoint POST tidak ditemukan"}, 404)
        except Exception as e:
            sys.stderr.write(f"\n--- SERVER ERROR IN POST {self.path} ---\n{traceback.format_exc()}\n")
            sys.stderr.flush()
            self._send_json({"status": "error", "message": str(e)}, 500)


def run_standalone_server(port=5000):
    server_address = ('', port)
    httpd = HTTPServer(server_address, MTMAPIHandler)
    print(f"Standalone REST API Server running on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    run_standalone_server()
