import os
import sys
import json
import traceback
from flask import Flask, request, jsonify, send_file, send_from_directory
from flask_cors import CORS

# Add backend directory to sys.path
base_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.append(base_dir)
from data_processor import MTMDataProcessor

app = Flask(__name__, static_folder=os.path.join(os.path.dirname(base_dir), 'frontend'))
CORS(app)  # Enable Cross-Origin Resource Sharing for Vercel/Render frontend integration

processor = MTMDataProcessor()
try:
    processor.load_data()
    print("Dataset loaded successfully on app startup.")
except Exception as e:
    print(f"Warning: Could not load initial dataset ({e}).")


@app.route("/", methods=["GET"])
def serve_index():
    frontend_dir = os.path.join(os.path.dirname(base_dir), 'frontend')
    if os.path.exists(os.path.join(frontend_dir, 'index.html')):
        return send_from_directory(frontend_dir, 'index.html')
    return jsonify({"status": "ok", "service": "SL MTM Analytics Backend"})


@app.route("/<path:path>", methods=["GET"])
def serve_static(path):
    frontend_dir = os.path.join(os.path.dirname(base_dir), 'frontend')
    target_path = os.path.join(frontend_dir, path)
    if os.path.exists(target_path) and not os.path.isdir(target_path):
        return send_from_directory(frontend_dir, path)
    if path.startswith("api/"):
        return jsonify({"status": "error", "message": "API endpoint not found"}), 404
    if os.path.exists(os.path.join(frontend_dir, 'index.html')):
        return send_from_directory(frontend_dir, 'index.html')
    return jsonify({"status": "error", "message": "Not found"}), 404


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "SL MTM Analytics Backend (Flask/Gunicorn)"})


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = str(data.get("username", "")).strip().lower()
    password = str(data.get("password", "")).strip()

    if username and password == "konimex123":
        role = "admin" if username == "admin" else "user"
        return jsonify({
            "status": "success",
            "user": {
                "username": username,
                "role": role,
                "can_upload": (role == "admin")
            },
            "token": f"token_{username}_12345"
        }), 200
    else:
        return jsonify({"status": "error", "message": "Username atau password salah! (Gunakan password: konimex123)"}), 401


@app.route("/api/data/filters", methods=["GET", "POST"])
def get_filters():
    try:
        req_data = request.get_json() if request.is_json else {}
        options = processor.get_filter_options(req_data)
        return jsonify({"status": "success", "data": options}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/analytics/kpi", methods=["POST"])
def get_kpi():
    data = request.get_json() or {}
    metric_type = data.get("metric_type", "idr")
    scorecard = processor.get_kpi_scorecard(data, metric_type=metric_type)
    return jsonify({"status": "success", "data": scorecard}), 200


@app.route("/api/analytics/trend", methods=["POST"])
def get_trend():
    data = request.get_json() or {}
    metric_type = data.get("metric_type", "idr")
    trend_data = processor.get_monthly_trend(data, metric_type=metric_type)
    return jsonify({"status": "success", "data": trend_data}), 200


@app.route("/api/analytics/pareto", methods=["POST"])
def get_pareto():
    data = request.get_json() or {}
    dimension = data.get("dimension", "alasan")
    metric_type = data.get("metric_type", "idr")
    unfulfill_only = data.get("unfulfill_only", True)
    pareto_data = processor.get_pareto_tree_maps(data, dimension=dimension, metric_type=metric_type, unfulfill_only=unfulfill_only)
    return jsonify({"status": "success", "data": pareto_data}), 200


@app.route("/api/analytics/grid", methods=["POST"])
def get_grid():
    data = request.get_json() or {}
    limit = int(data.get("limit", 500))
    dimension = data.get("dimension", "alasan")
    metric_type = data.get("metric_type", "idr")
    grid_data = processor.get_detail_grid(data, dimension=dimension, metric_type=metric_type, limit=limit)
    return jsonify({"status": "success", "data": grid_data}), 200


@app.route("/api/data/upload", methods=["POST"])
def upload_data():
    try:
        upload_password = request.headers.get("X-Upload-Password", "") or request.form.get("password", "") or request.args.get("password", "")
        if str(upload_password).strip() != "Adelle@0403":
            return jsonify({"status": "error", "message": "Password Akses Upload salah! Silakan masukan password Adelle@0403."}), 401

        target_month = request.headers.get("X-Target-Month", "") or request.form.get("target_month", "") or request.args.get("target_month", "")
        target_year = request.headers.get("X-Target-Year", "") or request.form.get("target_year", "") or request.args.get("target_year", "")
        target_month_num = request.form.get("target_month_num", "") or request.args.get("target_month_num", "")

        if not target_month and target_year and target_month_num:
            target_month = f"{target_year}-{int(target_month_num):02d}"

        if not target_month:
            return jsonify({"status": "error", "message": "Harap pilih Periode terlebih dahulu sebelum mengunggah data."}), 400

        if "file" not in request.files:
            return jsonify({"status": "error", "message": "File tidak ditemukan dalam request."}), 400

        file = request.files["file"]
        root_dir = os.path.dirname(base_dir)
        temp_dir = "/tmp" if (os.environ.get("VERCEL") or not os.access(root_dir, os.W_OK)) else root_dir
        temp_xlsx = os.path.join(temp_dir, f"temp_upload_{target_month.replace('-', '_')}.xlsx")
        target_db = processor.db_path

        file.save(temp_xlsx)

        from build_dataset_db_v2 import ingest_month_data
        res = ingest_month_data(xlsx_path=temp_xlsx, target_month=target_month, target_year=target_year, target_month_num=target_month_num, db_path=target_db)

        if os.path.exists(temp_xlsx):
            try: os.remove(temp_xlsx)
            except: pass

        if res.get("status") == "success":
            return jsonify(res), 200
        else:
            return jsonify({"status": "error", "message": res.get("message", "Penolakan verifikasi data.")}), 400
    except Exception as ex:
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"Gagal memproses upload: {str(ex)}"}), 500


@app.route("/api/export/ppt", methods=["POST"])
def export_ppt():
    try:
        data = request.get_json() or {}
        from ppt_exporter import MTMPPTExporter
        exporter = MTMPPTExporter()
        metric_type = data.get("metric_type", "idr")
        selected_modules = data.get("selected_modules", {"kpi_summary": True, "pareto_sheets": True, "detail_grid": True})

        months = data.get("months")
        if not months:
            single_m = data.get("month")
            months = [single_m] if single_m else ["2026-08"]
        if isinstance(months, str):
            months = [months]

        clean_months = sorted(list(set([str(m).strip() for m in months if m and str(m).strip()])))
        if not clean_months:
            clean_months = ["2026-08"]

        period_reports = []
        for m in clean_months:
            m_filters = dict(data)
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
            "filters": data,
            "period_reports": period_reports,
            "selected_modules": selected_modules
        }
        temp_dir = "/tmp" if (os.environ.get("VERCEL") or not os.access(base_dir, os.W_OK)) else base_dir
        output_file = os.path.join(temp_dir, "generated_mtm_report.pptx")
        exporter.generate_presentation(export_data, output_file)
        if os.path.exists(output_file):
            return send_file(output_file, as_attachment=True, download_name="Laporan_Service_Level_MTM.pptx", mimetype="application/vnd.openxmlformats-officedocument.presentationml.presentation")
        else:
            return jsonify({"status": "error", "message": "Gagal membuat file presentasi PPT"}), 500
    except Exception as ex:
        traceback.print_exc()
        return jsonify({"status": "error", "message": f"Gagal mengekspor PPT: {str(ex)}"}), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
