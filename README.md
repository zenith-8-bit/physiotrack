
# PhysioTrack 🎬📡

**AI-powered player movement intelligence for football, volleyball, and badminton.**
## a saas mvp that tracks player movements over an entiner game [football, volleyball, batminton, any other sport] to track player movement over an entire recorded game, a 3min highlight or a livestream of a game

Tracks players across a ≤3min video clip using YOLOv8 + ByteTrack, then routes the detection
output through an LLM reasoning layer (Claude) to select and run sport-specific analysis tools,
rendering everything in an interactive 3D trajectory viewer.

---

## Architecture

```
Video Input (≤3min)
    │
    ▼
tracker.py ── YOLOv8n + ByteTrack ──► per-frame player positions
    │                                  (x, y, player_id, speed, zone)
    ▼
llm_router.py ── Claude API ──────────► selects analysis tools
    │            (fallback: rule-based)  based on sport + tracking data
    ▼
tools/analysis_tools.py
    ├── trajectory      3D x/y/t paths, speed, total distance
    ├── heatmap         2D spatial density grid
    ├── zone_analysis   time-in-zone breakdown per player
    ├── speed_profile   static/walk/jog/sprint phase classification
    ├── player_proximity  close-encounter detection (marking, pressing)
    └── formation_snapshot  team positioning at key timestamps
    │
    ▼
app.py ── Flask web server ──────────► browser UI
    │
    ▼
templates/index.html
    ├── Three.js 3D trajectory view (time as Z-axis)
    ├── Canvas heatmap (per-player density)
    ├── Speed profile bars (phase-colored)
    └── Formation snapshot grid
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Web UI (recommended)
cd physiotrack
python app.py
# → http://localhost:5050

# CLI
python physiotrack_cli.py --video match_clip.mp4 --sport football

# Supported sports
--sport football    # 4-4-2, zones: defense / midfield / attack
--sport volleyball  # front/mid/back court + sides
--sport badminton   # front/mid/back + left/right
```

## Web UI Features

| Panel | What it shows |
|-------|---------------|
| **3D Trajectory** | Player paths with time as vertical axis. Orbit with mouse drag, scroll to zoom. Scrub timeline to animate. |
| **Heatmap** | Positional density grid per player — hotspot marked with glow. |
| **Speed Profile** | Per-frame speed bars colored by phase (static/walk/jog/sprint). |
| **Formation** | Minifield snapshots at 5 evenly-spaced timestamps. |

## LLM Tool Routing

After tracking, a summary (player count, sport, avg speed, zones seen) is sent to Claude.
The LLM responds with a JSON array of tool names to run:

```json
["trajectory", "heatmap", "zone_analysis", "player_proximity", "formation_snapshot"]
```

Falls back to rule-based selection if the API call fails.

## Extending

Add a new analysis tool in `tools/analysis_tools.py`:

```python
@tool("my_tool", "Description for the LLM to understand when to pick this")
def my_tool(data: dict) -> dict:
    # data has: player_tracks, raw_positions, sport, width, height, fps
    return {"tool": "my_tool", "result": ...}
```

The LLM will automatically discover it from the description.

## Roadmap

- [ ] Livestream input (RTSP / HLS)
- [ ] Ball detection + possession tracking
- [ ] Multi-camera stitching
- [ ] Export to CSV / PDF report
- [ ] Team color clustering for automatic team assignment
- [ ] Highlight clip generation at peak activity moments
