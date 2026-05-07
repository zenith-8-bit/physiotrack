"""
PhysioTrack - Analysis Tools
LLM-callable tools that compute sport-specific movement analytics.
Each tool takes a TrackingResult-like dict and returns structured JSON.
"""

import numpy as np
from collections import defaultdict
from typing import Dict, List, Any


# ── Tool registry ──────────────────────────────────────────────────────────────

TOOL_REGISTRY = {}


def tool(name: str, description: str):
    """Decorator to register a tool"""
    def decorator(fn):
        TOOL_REGISTRY[name] = {"fn": fn, "description": description}
        return fn
    return decorator


# ── Helpers ───────────────────────────────────────────────────────────────────

def _player_positions(data: dict) -> Dict[int, List[dict]]:
    """Extract player_tracks from raw tracking result"""
    return {int(k): v for k, v in data["player_tracks"].items()}


def _positions_array(positions: List[dict]) -> np.ndarray:
    """Returns Nx2 array of [x, y] normalized"""
    return np.array([[p["x"], p["y"]] for p in positions])


# ── Tools ─────────────────────────────────────────────────────────────────────

@tool("heatmap", "Generate a 2D spatial heatmap showing where each player spent most time")
def heatmap_tool(data: dict, grid_size: int = 20) -> dict:
    players = _player_positions(data)
    w, h = data["width"], data["height"]
    result = {}

    for pid, positions in players.items():
        grid = np.zeros((grid_size, grid_size), dtype=np.float32)
        for p in positions:
            gx = min(int(p["x"] * grid_size), grid_size - 1)
            gy = min(int(p["y"] * grid_size), grid_size - 1)
            grid[gy][gx] += 1

        # Normalize
        if grid.max() > 0:
            grid = grid / grid.max()

        # Find hotspot
        idx = np.unravel_index(np.argmax(grid), grid.shape)
        hotspot = {"grid_y": int(idx[0]), "grid_x": int(idx[1]),
                   "x_norm": round(idx[1] / grid_size, 2),
                   "y_norm": round(idx[0] / grid_size, 2)}

        result[str(pid)] = {
            "grid": grid.tolist(),
            "hotspot": hotspot,
            "total_frames": len(positions),
        }

    return {"tool": "heatmap", "grid_size": grid_size, "players": result}


@tool("trajectory", "Extract 3D movement trajectories [x, y, time] for each player")
def trajectory_tool(data: dict, smooth: bool = True, smooth_window: int = 5) -> dict:
    players = _player_positions(data)
    result = {}

    for pid, positions in players.items():
        xs = [p["x"] for p in positions]
        ys = [p["y"] for p in positions]
        ts = [p["timestamp"] for p in positions]
        speeds = [p.get("speed", 0) for p in positions]
        zones = [p.get("zone", "unknown") for p in positions]

        # Simple moving average smoothing
        if smooth and len(xs) >= smooth_window:
            kernel = np.ones(smooth_window) / smooth_window
            xs = np.convolve(xs, kernel, mode="same").tolist()
            ys = np.convolve(ys, kernel, mode="same").tolist()

        # Total distance
        pts = np.array(list(zip(xs, ys)))
        dists = np.linalg.norm(np.diff(pts, axis=0), axis=1)
        total_dist = float(np.sum(dists))

        result[str(pid)] = {
            "x": [round(v, 4) for v in xs],
            "y": [round(v, 4) for v in ys],
            "t": ts,
            "speed": speeds,
            "zones": zones,
            "total_distance_norm": round(total_dist, 4),
            "avg_speed": round(float(np.mean(speeds)), 2),
            "max_speed": round(float(np.max(speeds)) if speeds else 0, 2),
            "n_points": len(xs),
        }

    return {"tool": "trajectory", "players": result}


@tool("zone_analysis", "Analyze how much time each player spent in each court/field zone")
def zone_analysis_tool(data: dict) -> dict:
    players = _player_positions(data)
    result = {}

    for pid, positions in players.items():
        zone_counts = defaultdict(int)
        for p in positions:
            zone_counts[p.get("zone", "unknown")] += 1

        total = len(positions)
        zone_pct = {z: round(c / total * 100, 1) for z, c in zone_counts.items()}
        dominant_zone = max(zone_counts, key=zone_counts.get) if zone_counts else "unknown"

        result[str(pid)] = {
            "zone_counts": dict(zone_counts),
            "zone_percentages": zone_pct,
            "dominant_zone": dominant_zone,
            "total_frames": total,
        }

    return {"tool": "zone_analysis", "sport": data["sport"], "players": result}


@tool("speed_profile", "Compute speed timeline and classify movement phases (sprint, jog, walk, static)")
def speed_profile_tool(data: dict) -> dict:
    players = _player_positions(data)
    result = {}

    # Thresholds in px/sec (approximate)
    STATIC = 30
    WALK   = 100
    JOG    = 250
    # > JOG = sprint

    for pid, positions in players.items():
        speeds = [p.get("speed", 0) for p in positions]
        ts     = [p["timestamp"] for p in positions]

        phases = []
        for s in speeds:
            if s < STATIC:     phases.append("static")
            elif s < WALK:     phases.append("walk")
            elif s < JOG:      phases.append("jog")
            else:              phases.append("sprint")

        phase_counts = {p: phases.count(p) for p in ["static", "walk", "jog", "sprint"]}
        total = max(len(phases), 1)
        phase_pct = {p: round(c / total * 100, 1) for p, c in phase_counts.items()}

        result[str(pid)] = {
            "speeds": speeds,
            "timestamps": ts,
            "phases": phases,
            "phase_percentages": phase_pct,
            "avg_speed": round(float(np.mean(speeds)), 2),
            "max_speed": round(float(np.max(speeds)) if speeds else 0, 2),
            "sprint_count": sum(1 for i in range(1, len(phases)) if phases[i] == "sprint" and phases[i-1] != "sprint"),
        }

    return {"tool": "speed_profile", "players": result}


@tool("player_proximity", "Detect when players are close together — useful for marking, pressing, blocks")
def player_proximity_tool(data: dict, threshold: float = 0.08) -> dict:
    """threshold is in normalized coords (0-1)"""
    players = _player_positions(data)
    pids = list(players.keys())

    # Build frame->positions lookup
    frame_data = defaultdict(dict)
    for pid, positions in players.items():
        for p in positions:
            frame_data[p["frame"]][pid] = (p["x"], p["y"])

    events = []
    for frame, pos_map in sorted(frame_data.items()):
        pids_in_frame = list(pos_map.keys())
        for i in range(len(pids_in_frame)):
            for j in range(i + 1, len(pids_in_frame)):
                pa, pb = pids_in_frame[i], pids_in_frame[j]
                xa, ya = pos_map[pa]
                xb, yb = pos_map[pb]
                dist = np.sqrt((xa - xb)**2 + (ya - yb)**2)
                if dist < threshold:
                    events.append({
                        "frame": frame,
                        "player_a": pa,
                        "player_b": pb,
                        "distance": round(float(dist), 4),
                    })

    # Group by pair
    pair_counts = defaultdict(int)
    for e in events:
        pair_counts[f"{e['player_a']}-{e['player_b']}"] += 1

    return {
        "tool": "player_proximity",
        "threshold": threshold,
        "close_events": events[:200],   # cap for JSON size
        "total_close_frames": len(events),
        "top_pairs": dict(sorted(pair_counts.items(), key=lambda x: -x[1])[:10]),
    }


@tool("formation_snapshot", "Estimate team formation/positioning at key moments of the game")
def formation_snapshot_tool(data: dict, n_snapshots: int = 5) -> dict:
    players = _player_positions(data)
    if not players:
        return {"tool": "formation_snapshot", "snapshots": []}

    all_timestamps = sorted(set(
        p["timestamp"] for positions in players.values() for p in positions
    ))

    # Pick evenly spaced snapshot times
    step = max(1, len(all_timestamps) // n_snapshots)
    snap_times = [all_timestamps[i] for i in range(0, len(all_timestamps), step)][:n_snapshots]

    snapshots = []
    for t in snap_times:
        frame_positions = {}
        for pid, positions in players.items():
            # Find closest position to this timestamp
            closest = min(positions, key=lambda p: abs(p["timestamp"] - t))
            if abs(closest["timestamp"] - t) < 2.0:   # within 2 sec
                frame_positions[str(pid)] = {
                    "x": closest["x"],
                    "y": closest["y"],
                    "zone": closest.get("zone", "unknown"),
                }

        if frame_positions:
            xs = [v["x"] for v in frame_positions.values()]
            ys = [v["y"] for v in frame_positions.values()]
            snapshots.append({
                "timestamp": round(t, 2),
                "player_count": len(frame_positions),
                "positions": frame_positions,
                "centroid": {"x": round(float(np.mean(xs)), 3), "y": round(float(np.mean(ys)), 3)},
                "spread": round(float(np.std(xs + ys)), 3),
            })

    return {"tool": "formation_snapshot", "snapshots": snapshots}


def get_tool_descriptions() -> str:
    """Return formatted list of tools for LLM prompt"""
    lines = []
    for name, meta in TOOL_REGISTRY.items():
        lines.append(f"- {name}: {meta['description']}")
    return "\n".join(lines)


def run_tool(name: str, data: dict, **kwargs) -> dict:
    """Execute a tool by name"""
    if name not in TOOL_REGISTRY:
        return {"error": f"Unknown tool: {name}"}
    return TOOL_REGISTRY[name]["fn"](data, **kwargs)
