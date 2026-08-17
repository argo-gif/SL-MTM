import os
import sys
from flask import Flask, request, jsonify
from flask_cors import CORS

# Add backend directory to sys.path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from data_processor import MTMDataProcessor

app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing for frontend integration

# Initialize Data Processor
processor = MTMDataProcessor("uploaded_active_dataset.xlsx")

# Try loading data on startup
try:
    processor.load_data()
    print("Dataset loaded successfully on app startup.")
except Exception as e:
    print(f"Warning: Could not load initial dataset ({e}). Waiting for upload or local dataset.")


@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({"status": "ok", "service": "SL MTM Analytics Backend"})


@app.route("/api/auth/login", methods=["POST"])
def login():
    data = request.get_json() or {}
    username = str(data.get("username", "")).strip().lower()
    password = str(data.get("password", "")).strip()

    if username in ["admin", "konimex"] and password == "konimex123":
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
        return jsonify({"status": "error", "message": "Username atau password salah!"}), 401


@app.route("/api/data/upload", methods=["POST"])
def upload_data():
    role = request.headers.get("X-User-Role", "user")
    if role != "admin":
        return jsonify({"status": "error", "message": "Akses ditolak: Hanya role admin yang dapat mengunggah data."}), 403

    if "file" not in request.files:
        return jsonify({"status": "error", "message": "File tidak ditemukan dalam request."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"status": "error", "message": "Nama file kosong."}), 400

    save_path = "uploaded_active_dataset.xlsx"
    file.save(save_path)
    
    # Reload processor with new dataset
    try:
        processor.data_path = save_path
        processor.load_data()
        return jsonify({"status": "success", "message": "Dataset Excel berhasil diunggah dan diperbarui."}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": f"Gagal membaca file Excel: {str(e)}"}), 500


@app.route("/api/data/filters", methods=["GET"])
def get_filters():
    try:
        options = processor.get_filter_options()
        return jsonify({"status": "success", "data": options}), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route("/api/analytics/kpi", methods=["POST"])
def get_kpi():
    data = request.get_json() or {}
    metric_type = data.get("metric_type", "idr")
    
    filtered_df = processor.filter_data(data)
    scorecard = processor.get_kpi_scorecard(filtered_df, metric_type=metric_type)
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
    
    filtered_df = processor.filter_data(data)
    pareto_data = processor.get_pareto_tree_maps(filtered_df, dimension=dimension, metric_type=metric_type)
    return jsonify({"status": "success", "dimension": dimension, "data": pareto_data}), 200


@app.route("/api/analytics/grid", methods=["POST"])
def get_grid():
    data = request.get_json() or {}
    limit = data.get("limit", 500)
    
    filtered_df = processor.filter_data(data)
    records = processor.get_detail_grid(filtered_df, limit=limit)
    return jsonify({"status": "success", "count": len(records), "data": records}), 200


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
