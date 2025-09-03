# app.py

import json
import threading
from datetime import datetime
from pathlib import Path

from flask import (
    Flask, request, redirect, url_for, send_from_directory,
    render_template, jsonify
)

from ocr_processor import extract_ocr_subtitles
from translator import translate_chinese_to_ja
from config import FRAME_INTERVAL

app = Flask(__name__)
BASE_DIR = Path(__file__).resolve().parent
UPLOAD_DIR = BASE_DIR / "uploads"
RESULT_DIR = BASE_DIR / "results"
for d in (UPLOAD_DIR, RESULT_DIR):
    d.mkdir(parents=True, exist_ok=True)

# job_id: {"status","progress","result","video","phase","last_error"}
JOBS = {}

@app.after_request
def add_no_cache_headers(resp):
    try:
        if request.path.startswith("/status/") or request.path.startswith("/exists/"):
            resp.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
            resp.headers["Pragma"] = "no-cache"
            resp.headers["Expires"] = "0"
    except Exception:
        pass
    return resp

def _safe_filename(name: str) -> str:
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    base = Path(name).stem[:40]
    return f"{ts}_{base}.mp4"

@app.route("/")
def index():
    return render_template("upload.html")

@app.route("/analyze", methods=["POST"])
def analyze():
    file = request.files.get("video")
    if not file:
        return redirect(url_for("index"))

    fname = _safe_filename(file.filename)
    dst = UPLOAD_DIR / fname
    file.save(dst)

    job_id = dst.stem
    JOBS[job_id] = {"status": "queued", "progress": 0.0, "result": None,
                    "video": str(dst), "phase": "queued", "last_error": ""}

    def _worker():
        try:
            JOBS[job_id].update(status="running", phase="OCR中", progress=0.001)

            # OCR
            raw = extract_ocr_subtitles(str(dst), interval=FRAME_INTERVAL)

            # 翻訳
            JOBS[job_id]["phase"] = "翻訳中"
            JOBS[job_id]["progress"] = max(JOBS[job_id]["progress"], 0.05)

            out = []
            total = len(raw) if raw else 0
            if total == 0:
                json_path = RESULT_DIR / f"{job_id}.json"
                json_path.write_text(json.dumps([], ensure_ascii=False, indent=2), encoding="utf-8")
                JOBS[job_id].update(status="done", result=str(json_path), progress=1.0, phase="完了")
                return

            for idx, item in enumerate(raw, 1):
                zh = item.get("text", "")
                ts = float(item.get("timestamp", 0) or 0)
                try:
                    ja = translate_chinese_to_ja(zh)
                except Exception as e:
                    ja = "(翻訳失敗)"
                    JOBS[job_id]["last_error"] = str(e)
                out.append({"timestamp": ts, "zh": zh, "ja": ja})
                JOBS[job_id]["progress"] = 0.05 + 0.90 * (idx / total)

            out.sort(key=lambda x: x["timestamp"])
            json_path = RESULT_DIR / f"{job_id}.json"
            json_path.write_text(json.dumps(out, ensure_ascii=False, indent=2), encoding="utf-8")

            JOBS[job_id].update(status="done", result=str(json_path), progress=1.0, phase="完了")
        except Exception as e:
            JOBS[job_id]["status"] = f"error: {e}"
            JOBS[job_id]["last_error"] = str(e)

    threading.Thread(target=_worker, daemon=True).start()
    return redirect(url_for("progress_view", job_id=job_id))

@app.route("/progress/<job_id>")
def progress_view(job_id):
    return render_template("progress.html", job_id=job_id)

@app.route("/status/<job_id>")
def status(job_id):
    info = JOBS.get(job_id)
    if not info:
        return jsonify({"progress": 0, "status": "unknown", "phase": "", "last_error": ""})
    return jsonify({
        "progress": float(info.get("progress", 0)),
        "status": info.get("status", "running"),
        "phase": info.get("phase", ""),
        "last_error": info.get("last_error", "")
    })

@app.route("/exists/<job_id>")
def exists(job_id):
    return jsonify({"exists": (RESULT_DIR / f"{job_id}.json").exists()})

@app.route("/view/<job_id>")
def view(job_id):
    json_path = RESULT_DIR / f"{job_id}.json"
    if not json_path.exists():
        return redirect(url_for("progress_view", job_id=job_id))
    data = json.loads(json_path.read_text(encoding="utf-8"))

    src = None
    info = JOBS.get(job_id)
    if info and info.get("video") and Path(info["video"]).exists():
        src = url_for("uploaded_file", filename=f"{job_id}.mp4")

    return render_template("lyric.html", data=data, job_id=job_id, src=src)

@app.route("/uploads/<path:filename>")
def uploaded_file(filename):
    return send_from_directory(UPLOAD_DIR, filename)

@app.route("/results/<job_id>.json")
def json_result(job_id):
    p = RESULT_DIR / f"{job_id}.json"
    if not p.exists():
        info = JOBS.get(job_id, {})
        return jsonify({"status": info.get("status", "unknown"), "progress": info.get("progress", 0)})
    return send_from_directory(RESULT_DIR, f"{job_id}.json")

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
