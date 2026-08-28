import os
import sys
import json
import traceback
from http.server import HTTPServer, ThreadingHTTPServer, BaseHTTPRequestHandler
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
        try:
            body = json.dumps(data).encode('utf-8')
            self.send_response(status_code)
            self._send_cors_headers()
            self.send_header('Content-Type', 'application/json')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Connection', 'close')
            self.end_headers()
            self.wfile.write(body)
            self.wfile.flush()
        except Exception as e:
            print("Socket response notice:", e)

    def do_GET(self):
        try:
            parsed = urlparse(self.path)
            path = parsed.path
            
            if path == '/api/health':
                self._send_json({"status": "ok", "service": "SL MTM Analytics Backend (Standalone)"})
            elif path == '/api/data/filters':
                parsed_qs = parse_qs(parsed.query)
                filters = {}
                for k, v in parsed_qs.items():
                    filters[k] = v[0] if len(v) == 1 else v
                options = processor.get_filter_options(filters)
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


            elif path == '/api/data/filters':
                options = processor.get_filter_options(req_data)
                self._send_json({"status": "success", "data": options})

            elif path == '/api/analytics/grid':
                limit = int(req_data.get("limit", 500))
                dimension = req_data.get("dimension", "alasan")
                metric_type = req_data.get("metric_type", "idr")
                grid_data = processor.get_detail_grid(req_data, dimension=dimension, metric_type=metric_type, limit=limit)
                self._send_json({"status": "success", "data": grid_data})


            elif path.startswith('/api/data/upload'):
                try:
                    parsed_url = urlparse(self.path)
                    params = parse_qs(parsed_url.query)
                    target_month = params.get('target_month', [''])[0] or params.get('month', [''])[0] or self.headers.get('X-Target-Month', '')
                    target_year = params.get('target_year', [''])[0] or params.get('year', [''])[0] or self.headers.get('X-Target-Year', '')
                    target_month_num = params.get('target_month_num', [''])[0] or params.get('month_num', [''])[0]
                    upload_password = params.get('password', [''])[0] or self.headers.get('X-Upload-Password', '')

                    content_length = int(self.headers.get('Content-Length', 0))
                    content_type = self.headers.get('Content-Type', '')

                    raw_chunks = []
                    bytes_read = 0
                    while bytes_read < content_length:
                        chunk_size = min(65536, content_length - bytes_read)
                        chunk = self.rfile.read(chunk_size)
                        if not chunk:
                            break
                        raw_chunks.append(chunk)
                        bytes_read += len(chunk)

                    raw_body = b''.join(raw_chunks)

                    if not raw_body or len(raw_body) == 0:
                        self._send_json({"status": "error", "message": "Payload upload kosong."}, 400)
                        return

                    file_bytes = raw_body
                    if 'multipart/form-data' in content_type:
                        try:
                            b_str = content_type.split('boundary=')[-1].split(';')[0].strip()
                            if b_str.startswith('"') and b_str.endswith('"'):
                                b_str = b_str[1:-1]
                            boundary = b_str.encode()
                            parts = raw_body.split(b'--' + boundary)
                            for part in parts:
                                if b'Content-Disposition:' in part:
                                    if b'name="password"' in part or b'name="upload_password"' in part:
                                        body_lines = part.split(b'\r\n\r\n', 1)
                                        if len(body_lines) > 1:
                                            p_val = body_lines[1].split(b'\r\n')[0].decode('utf-8', errors='ignore').strip()
                                            if p_val: upload_password = p_val
                                    elif b'name="target_year"' in part or b'name="year"' in part:
                                        body_lines = part.split(b'\r\n\r\n', 1)
                                        if len(body_lines) > 1:
                                            y_val = body_lines[1].split(b'\r\n')[0].decode('utf-8', errors='ignore').strip()
                                            if y_val: target_year = y_val
                                    elif b'name="target_month_num"' in part or b'name="month_num"' in part:
                                        body_lines = part.split(b'\r\n\r\n', 1)
                                        if len(body_lines) > 1:
                                            mn_val = body_lines[1].split(b'\r\n')[0].decode('utf-8', errors='ignore').strip()
                                            if mn_val: target_month_num = mn_val
                                    elif b'name="target_month"' in part or b'name="month"' in part:
                                        body_lines = part.split(b'\r\n\r\n', 1)
                                        if len(body_lines) > 1:
                                            m_val = body_lines[1].split(b'\r\n')[0].decode('utf-8', errors='ignore').strip()
                                            if m_val: target_month = m_val
                                    elif b'filename=' in part or b'name="file"' in part:
                                        body_lines = part.split(b'\r\n\r\n', 1)
                                        if len(body_lines) > 1:
                                            fdata = body_lines[1]
                                            pk_start = fdata.find(b'PK\x03\x04')
                                            if pk_start != -1:
                                                fdata = fdata[pk_start:]
                                                while fdata and fdata[-1:] in (b'\r', b'\n', b'-', b' '):
                                                    fdata = fdata[:-1]
                                            file_bytes = fdata
                        except Exception as m_ex:
                            sys.stderr.write(f"Multipart parsing notice: {m_ex}\n")

                    if str(upload_password).strip() != "Adelle@0403":
                        self._send_json({"status": "error", "message": "Password Akses Upload salah! Silakan masukan password Adelle@0403."}, 401)
                        return

                    target_month = str(target_month).strip()
                    if not target_month and target_year and target_month_num:
                        target_month = f"{target_year}-{int(target_month_num):02d}"

                    if not target_month:
                        self._send_json({"status": "error", "message": "Harap pilih Periode terlebih dahulu sebelum mengunggah data."}, 400)
                        return

                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    temp_xlsx = os.path.join(base_dir, f"temp_upload_{target_month.replace('-', '_')}.xlsx")
                    target_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset.db")

                    with open(temp_xlsx, 'wb') as f:
                        f.write(file_bytes)

                    from build_dataset_db_v2 import ingest_month_data
                    res = ingest_month_data(xlsx_path=temp_xlsx, target_month=target_month, target_year=target_year, target_month_num=target_month_num, db_path=target_db)

                    if res.get("status") == "success":
                        if os.path.exists(temp_xlsx):
                            try: os.remove(temp_xlsx)
                            except: pass
                        self._send_json(res, 200)
                    else:
                        sys.stderr.write(f"\n[UPLOAD REJECTED] {res}\n")
                        sys.stderr.flush()
                        self._send_json({"status": "error", "message": res.get("message", "Penolakan verifikasi data.")}, 400)
                except Exception as ex:
                    traceback.print_exc()
                    self._send_json({"status": "error", "message": f"Gagal memproses upload: {str(ex)}"}, 500)

            elif path.startswith('/api/data/import-local'):
                try:
                    parsed_url = urlparse(self.path)
                    params = parse_qs(parsed_url.query)
                    target_month = params.get('target_month', [''])[0] or self.headers.get('X-Target-Month', '2026-08')
                    upload_password = params.get('password', [''])[0] or self.headers.get('X-Upload-Password', '')

                    if str(upload_password).strip() != "Adelle@0403":
                        self._send_json({"status": "error", "message": "Password Akses Upload salah! Masukkan Adelle@0403."}, 401)
                        return

                    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    
                    import glob
                    all_xlsx = [
                        f for f in glob.glob(os.path.join(base_dir, "*.xlsx"))
                        if not os.path.basename(f).startswith('~$')
                    ]
                    
                    user_files = [f for f in all_xlsx if os.path.basename(f) != "uploaded_active_dataset.xlsx"]
                    
                    found_file = None
                    if user_files:
                        user_files.sort(key=lambda f: os.path.getmtime(f), reverse=True)
                        found_file = user_files[0]
                    elif all_xlsx:
                        found_file = all_xlsx[0]

                    if not found_file:
                        self._send_json({"status": "error", "message": f"Tidak ada file Excel di folder [{base_dir}]. Silakan salin file Excel ke folder tersebut."}, 404)
                        return

                    filename = os.path.basename(found_file)
                    target_db = os.path.join(os.path.dirname(os.path.abspath(__file__)), "dataset.db")
                    from build_dataset_db_v2 import ingest_month_data
                    res = ingest_month_data(xlsx_path=found_file, target_month=target_month, db_path=target_db)
                    
                    if res.get("status") == "success":
                        res["message"] = f"Berhasil mengimpor {res.get('inserted_count', 0):,} baris dari file [{filename}] untuk periode [{target_month}]!"
                        self._send_json(res, 200)
                    else:
                        self._send_json(res, 400)
                except Exception as ex:
                    traceback.print_exc()
                    self._send_json({"status": "error", "message": f"Gagal import file lokal: {str(ex)}"}, 500)

            elif path == '/api/export/ppt':

                try:
                    from ppt_exporter import MTMPPTExporter
                    exporter = MTMPPTExporter()
                    metric_type = req_data.get("metric_type", "idr")
                    selected_modules = req_data.get("selected_modules", {"kpi_summary": True, "pareto_sheets": True, "detail_grid": True})

                    months = req_data.get("months")
                    if not months:
                        single_m = req_data.get("month")
                        months = [single_m] if single_m else ["2026-08"]
                    if isinstance(months, str):
                        months = [months]

                    clean_months = sorted(list(set([str(m).strip() for m in months if m and str(m).strip()])))
                    if not clean_months:
                        clean_months = ["2026-08"]

                    period_reports = []
                    for m in clean_months:
                        m_filters = dict(req_data)
                        m_filters["month"] = m
                        m_filters["months"] = [m]

                        rep = {
                            "filters": m_filters,
                            "kpi": processor.get_kpi_scorecard(m_filters, metric_type=metric_type),
                            "trend": processor.get_monthly_trend(m_filters, metric_type=metric_type),
                            "pareto": {
                                "alasan": processor.get_pareto_tree_maps(m_filters, dimension="alasan", metric_type=metric_type),
                                "mtm_alias": processor.get_pareto_tree_maps(m_filters, dimension="mtm_alias", metric_type=metric_type),
                                "cabang": processor.get_pareto_tree_maps(m_filters, dimension="cabang", metric_type=metric_type),
                                "grup_brand": processor.get_pareto_tree_maps(m_filters, dimension="grup_brand", metric_type=metric_type),
                                "item": processor.get_pareto_tree_maps(m_filters, dimension="item", metric_type=metric_type),
                            },
                            "grid_by_dim": {
                                "alasan": processor.get_detail_grid(m_filters, dimension="alasan", metric_type=metric_type, limit=200),
                                "mtm_alias": processor.get_detail_grid(m_filters, dimension="mtm_alias", metric_type=metric_type, limit=200),
                                "cabang": processor.get_detail_grid(m_filters, dimension="cabang", metric_type=metric_type, limit=200),
                                "grup_brand": processor.get_detail_grid(m_filters, dimension="grup_brand", metric_type=metric_type, limit=200),
                                "item": processor.get_detail_grid(m_filters, dimension="item", metric_type=metric_type, limit=200),
                            },
                            "grid": processor.get_detail_grid(m_filters, limit=50),
                            "selected_modules": selected_modules
                        }
                        period_reports.append(rep)

                    export_data = {
                        "filters": req_data,
                        "period_reports": period_reports,
                        "selected_modules": selected_modules
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
    httpd = ThreadingHTTPServer(server_address, MTMAPIHandler)
    print(f"Standalone REST API Server running on port {port}...")
    httpd.serve_forever()

if __name__ == '__main__':
    run_standalone_server()
