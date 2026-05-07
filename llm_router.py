"""
PhysioTrack - LLM Reasoning Layer
Uses Anthropic Claude (or falls back to rule-based) to decide which
analysis tools to run based on tracking output and sport context.
"""

import json
import os
import requests
from typing import List, Dict, Any


SYSTEM_PROMPT = """You are a sports analytics AI assistant. You are given a summary of player tracking data
extracted from a video clip of a sport match. Your job is to decide which analysis tools to run
to produce the most insightful visualizations and statistics.

Available tools:
{tool_list}

Based on the sport, number of players detected, and tracking quality, output a JSON array of tool names to run.
Only output the JSON array, nothing else. Example: ["trajectory", "heatmap", "zone_analysis"]

Rules:
- Always include "trajectory" and "heatmap" as they are fundamental
- For team sports (football, volleyball) with 4+ players, add "player_proximity" and "formation_snapshot"  
- For racket sports (badminton) with 2 players, add "speed_profile"
- Add "zone_analysis" for any sport with defined zones
- Add "speed_profile" if avg speed data shows significant variation
- Maximum 5 tools total
"""


def build_tracking_summary(tracking_data: dict) -> str:
    """Build a concise summary of tracking results for the LLM"""
    n_players = len(tracking_data.get("player_tracks", {}))
    sport = tracking_data.get("sport", "unknown")
    duration = tracking_data.get("duration_seconds", 0)
    n_positions = len(tracking_data.get("raw_positions", []))

    speeds = [p.get("speed", 0) for p in tracking_data.get("raw_positions", [])]
    avg_speed = sum(speeds) / max(len(speeds), 1)
    max_speed = max(speeds) if speeds else 0

    zones_seen = set(p.get("zone", "") for p in tracking_data.get("raw_positions", []))

    return f"""
Sport: {sport}
Duration: {duration:.1f} seconds  
Players detected: {n_players}
Total position samples: {n_positions}
Average movement speed: {avg_speed:.1f} px/sec
Max speed recorded: {max_speed:.1f} px/sec
Zones observed: {', '.join(z for z in zones_seen if z)}
Frame resolution: {tracking_data.get('width', 0)}x{tracking_data.get('height', 0)}
""".strip()


def llm_select_tools(tracking_data: dict, tool_descriptions: str) -> List[str]:
    """
    Use Claude API to select which tools to run.
    Falls back to rule-based selection if API fails.
    """
    summary = build_tracking_summary(tracking_data)
    sport = tracking_data.get("sport", "football")
    n_players = len(tracking_data.get("player_tracks", {}))

    prompt = f"""Tracking data summary:
{summary}

Select the best analysis tools to run for maximum insight."""

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 200,
                "system": SYSTEM_PROMPT.format(tool_list=tool_descriptions),
                "messages": [{"role": "user", "content": prompt}],
            },
            timeout=15,
        )

        if response.status_code == 200:
            data = response.json()
            raw = data["content"][0]["text"].strip()
            # Parse JSON array from response
            tools = json.loads(raw)
            if isinstance(tools, list):
                print(f"[LLM] Selected tools: {tools}")
                return tools

    except Exception as e:
        print(f"[LLM] API call failed: {e}, falling back to rule-based selection")

    # Rule-based fallback
    return _rule_based_selection(sport, n_players)


def _rule_based_selection(sport: str, n_players: int) -> List[str]:
    """Deterministic tool selection fallback"""
    tools = ["trajectory", "heatmap", "zone_analysis"]

    if sport in ("football", "volleyball") and n_players >= 4:
        tools.append("formation_snapshot")
        tools.append("player_proximity")
    elif sport == "badminton":
        tools.append("speed_profile")
    else:
        tools.append("speed_profile")

    return tools[:5]


def generate_insights(analysis_results: dict, sport: str) -> str:
    """
    Use Claude to generate natural language insights from analysis results.
    """
    # Build a compact summary of results (avoid sending huge arrays)
    compact = {}

    for tool_name, result in analysis_results.items():
        if tool_name == "trajectory":
            compact[tool_name] = {
                pid: {
                    "avg_speed": data.get("avg_speed"),
                    "max_speed": data.get("max_speed"),
                    "total_distance": data.get("total_distance_norm"),
                    "n_points": data.get("n_points"),
                }
                for pid, data in result.get("players", {}).items()
            }
        elif tool_name == "zone_analysis":
            compact[tool_name] = {
                pid: {
                    "dominant_zone": data.get("dominant_zone"),
                    "zone_percentages": data.get("zone_percentages"),
                }
                for pid, data in result.get("players", {}).items()
            }
        elif tool_name == "speed_profile":
            compact[tool_name] = {
                pid: {
                    "phase_percentages": data.get("phase_percentages"),
                    "sprint_count": data.get("sprint_count"),
                    "max_speed": data.get("max_speed"),
                }
                for pid, data in result.get("players", {}).items()
            }
        elif tool_name == "player_proximity":
            compact[tool_name] = {
                "total_close_events": result.get("total_close_frames"),
                "top_pairs": result.get("top_pairs"),
            }
        elif tool_name == "formation_snapshot":
            snaps = result.get("snapshots", [])
            compact[tool_name] = {
                "n_snapshots": len(snaps),
                "avg_spread": round(
                    sum(s.get("spread", 0) for s in snaps) / max(len(snaps), 1), 3
                ) if snaps else 0,
            }

    insight_prompt = f"""You are a sports analyst. Here is player movement analysis data from a {sport} match clip:

{json.dumps(compact, indent=2)}

Write 3-5 concise bullet-point insights about player movement, positioning, and performance patterns.
Be specific with numbers. Keep each bullet under 2 sentences."""

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={
                "Content-Type": "application/json",
                "anthropic-version": "2023-06-01",
            },
            json={
                "model": "claude-sonnet-4-20250514",
                "max_tokens": 500,
                "messages": [{"role": "user", "content": insight_prompt}],
            },
            timeout=15,
        )

        if response.status_code == 200:
            data = response.json()
            return data["content"][0]["text"].strip()

    except Exception as e:
        print(f"[LLM] Insights generation failed: {e}")

    return _fallback_insights(compact, sport)


def _fallback_insights(compact: dict, sport: str) -> str:
    lines = [f"• Sport: {sport} analysis complete."]

    traj = compact.get("trajectory", {})
    if traj:
        speeds = [v.get("avg_speed", 0) for v in traj.values() if v.get("avg_speed")]
        if speeds:
            lines.append(f"• Average player speed: {sum(speeds)/len(speeds):.1f} px/sec across {len(speeds)} tracked players.")

    zones = compact.get("zone_analysis", {})
    for pid, zdata in list(zones.items())[:2]:
        dom = zdata.get("dominant_zone", "")
        if dom:
            lines.append(f"• Player {pid} spent most time in the {dom} zone.")

    speed_p = compact.get("speed_profile", {})
    for pid, sdata in list(speed_p.items())[:1]:
        phases = sdata.get("phase_percentages", {})
        sprint_pct = phases.get("sprint", 0)
        lines.append(f"• Player {pid} sprinted {sprint_pct}% of the time, with {sdata.get('sprint_count', 0)} sprint bursts.")

    return "\n".join(lines)
