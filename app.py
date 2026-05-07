"""
PhysioTrack - Flask Backend
Handles video upload, tracking pipeline, LLM routing, analysis
"""

import os
import json
import uuid
import threading
from pathlib import Path
from flask import Flask, request, jsonify, render_template, send_from_directory

from tracker import run_tracking, TrackingResult
from tools.analysis_tools import get_tool_descriptions, run_tool
from llm_router import llm_select_tools, generate_insights

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 500 * 1024 * 1024   # 500MB

UPLOAD_DIR = Path("uploads")
OUTPUT_DIR = Path("output")
UPLOAD_DIR.mkdir(exist_ok=True)
OUTPUT_DIR.mkdir(exist_ok=True)

# In-memory job store (use Redis in prod)
jobs: dict = {}


def process_video_job(job_id: str, video_path: str, sport: str):
    """Background thread: track → route → analyze → insights"""
    try:
        jobs[job_id]["status"] = "tracking"
        jobs[job_id]["progress"] = 5

        def progress_cb(pct, frame, processed):
            jobs[job_id]["progress"] = 5 + int(pct * 0.6)   # 5-65%
            jobs[job_id]["frame"] = frame

        tracking = run_tracking(video_path, sport=sport, sample_every=3, progress_callback=progress_cb)

        # Serialize tracking result
        tracking_data = {
            "sport": tracking.sport,
            "total_frames": tracking.total_frames,
            "fps": tracking.fps,
            "duration_seconds": tracking.duration_seconds,
            "width": tracking.width,
            "height": tracking.height,
            "player_tracks": tracking.player_tracks,
            "frame_sample_rate": tracking.frame_sample_rate,
            "raw_positions": tracking.raw_positions,
        }

        jobs[job_id]["status"] = "routing"
        jobs[job_id]["progress"] = 65
        jobs[job_id]["player_count"] = len(tracking.player_tracks)

        # LLM selects tools
        tool_descs = get_tool_descriptions()
        selected_tools = llm_select_tools(tracking_data, tool_descs)
        jobs[job_id]["selected_tools"] = selected_tools
        jobs[job_id]["progress"] = 70

        # Run tools
        jobs[job_id]["status"] = "analyzing"
        analysis = {}
        for i, tool_name in enumerate(selected_tools):
            result = run_tool(tool_name, tracking_data)
            analysis[tool_name] = result
            jobs[job_id]["progress"] = 70 + int((i + 1) / len(selected_tools) * 20)

        # Generate LLM insights
        jobs[job_id]["status"] = "generating_insights"
        jobs[job_id]["progress"] = 92
        insights = generate_insights(analysis, sport)

        # Build final payload (trim raw_positions for response size)
        payload = {
            "job_id": job_id,
            "sport": sport,
            "duration": tracking.duration_seconds,
            "fps": tracking.fps,
            "resolution": {"w": tracking.width, "h": tracking.height},
            "player_count": len(tracking.player_tracks),
            "player_ids": list(tracking.player_tracks.keys()),
            "selected_tools": selected_tools,
            "analysis": analysis,
            "insights": insights,
            "tracking_summary": {
                pid: {
                    "n_frames": len(positions),
                    "first_seen": positions[0]["timestamp"] if positions else 0,
                    "last_seen": positions[-1]["timestamp"] if positions else 0,
                }
                for pid, positions in tracking.player_tracks.items()
            }
        }

        # Save to disk
        out_path = OUTPUT_DIR / f"{job_id}.json"
        with open(out_path, "w") as f:
            json.dump(payload, f)

        jobs[job_id]["status"] = "done"
        jobs[job_id]["progress"] = 100
        jobs[job_id]["result_path"] = str(out_path)

    except Exception as e:
        import traceback
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)
        jobs[job_id]["traceback"] = traceback.format_exc()
        print(f"[ERROR] Job {job_id}: {e}")
        traceback.print_exc()


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/upload", methods=["POST"])
def upload():
    if "video" not in request.files:
        return jsonify({"error": "No video file"}), 400

    file = request.files["video"]
    sport = request.form.get("sport", "football")

    if file.filename == "":
        return jsonify({"error": "Empty filename"}), 400

    ext = Path(file.filename).suffix.lower()
    if ext not in (".mp4", ".avi", ".mov", ".mkv", ".webm"):
        return jsonify({"error": "Unsupported format"}), 400

    job_id = str(uuid.uuid4())[:8]
    save_path = UPLOAD_DIR / f"{job_id}{ext}"
    file.save(str(save_path))

    jobs[job_id] = {
        "status": "queued",
        "progress": 0,
        "sport": sport,
        "filename": file.filename,
        "job_id": job_id,
    }

    thread = threading.Thread(
        target=process_video_job,
        args=(job_id, str(save_path), sport),
        daemon=True,
    )
    thread.start()

    return jsonify({"job_id": job_id})


@app.route("/api/status/<job_id>")
def status(job_id):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job not found"}), 404
    return jsonify(job)


@app.route("/api/result/<job_id>")
def result(job_id):
    out_path = OUTPUT_DIR / f"{job_id}.json"
    if not out_path.exists():
        return jsonify({"error": "Result not ready"}), 404
    with open(out_path) as f:
        return jsonify(json.load(f))


@app.route("/api/demo/<sport>")
def demo_result(sport):
    """Return synthetic demo data for UI testing"""
    import random
    import math

    random.seed(42)
    sport = sport if sport in ("football", "volleyball", "badminton") else "football"

    n_players = {"football": 6, "volleyball": 4, "badminton": 2}[sport]
    duration = 45.0
    fps = 30

    player_tracks = {}
    raw_positions = []

    for pid in range(1, n_players + 1):
        positions = []
        x, y = random.random(), random.random()
        speed_base = random.uniform(50, 200)

        for t in range(0, int(duration * 10), 3):
            ts = t / 10.0
            # Simulate player movement
            x += random.gauss(0, 0.015)
            y += random.gauss(0, 0.015)
            x = max(0.02, min(0.98, x))
            y = max(0.02, min(0.98, y))

            speed = speed_base + random.gauss(0, 30)
            if random.random() < 0.1:
                speed = random.uniform(300, 500)

            zone_x = "left" if x < 0.33 else ("center" if x < 0.66 else "right")
            zone_y = "defense" if y < 0.33 else ("midfield" if y < 0.66 else "attack")
            zone = f"{zone_y}" if sport == "football" else zone_x

            pos = {
                "frame": int(ts * fps),
                "timestamp": round(ts, 3),
                "player_id": pid,
                "x": round(x, 4),
                "y": round(y, 4),
                "x_px": int(x * 1280),
                "y_px": int(y * 720),
                "width": 60,
                "height": 120,
                "confidence": round(random.uniform(0.6, 0.99), 3),
                "speed": round(max(0, speed), 2),
                "zone": zone,
            }
            positions.append(pos)
            raw_positions.append(pos)

        player_tracks[pid] = positions

    # Build fake analysis
    from tools.analysis_tools import run_tool
    tracking_data = {
        "sport": sport, "player_tracks": player_tracks,
        "raw_positions": raw_positions, "width": 1280, "height": 720,
        "fps": fps, "duration_seconds": duration,
        "total_frames": int(duration * fps), "frame_sample_rate": 3,
    }

    analysis = {
        "trajectory": run_tool("trajectory", tracking_data),
        "heatmap": run_tool("heatmap", tracking_data),
        "zone_analysis": run_tool("zone_analysis", tracking_data),
        "speed_profile": run_tool("speed_profile", tracking_data),
    }

    if n_players >= 4:
        analysis["formation_snapshot"] = run_tool("formation_snapshot", tracking_data)

    return jsonify({
        "job_id": "demo",
        "sport": sport,
        "duration": duration,
        "fps": fps,
        "resolution": {"w": 1280, "h": 720},
        "player_count": n_players,
        "player_ids": list(range(1, n_players + 1)),
        "selected_tools": list(analysis.keys()),
        "analysis": analysis,
        "insights": f"""• Players showed highly varied movement intensity — peak speeds exceeded 400 px/sec during sprint phases.
• The midfield zone was the most contested area, with 3 of {n_players} players spending >40% of time there.
• Player clustering events occurred frequently, suggesting active pressing or marking sequences.
• Sprint bursts averaged 4-6 per player over the {int(duration)}s clip, consistent with high-intensity interval play.
• Positional spread increased toward the final third, indicating a more attacking phase of play.""",
        "tracking_summary": {
            pid: {"n_frames": len(pos), "first_seen": pos[0]["timestamp"], "last_seen": pos[-1]["timestamp"]}
            for pid, pos in player_tracks.items()
        }
    })


if __name__ == "__main__":
    app.run(debug=True, port=5050)
