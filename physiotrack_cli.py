#!/usr/bin/env python3
"""
PhysioTrack CLI
Usage:
    python physiotrack_cli.py --video path/to/clip.mp4 --sport football
    python physiotrack_cli.py --video clip.mp4 --sport badminton --output results.json
"""

import argparse
import json
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from tracker import run_tracking
from tools.analysis_tools import get_tool_descriptions, run_tool
from llm_router import llm_select_tools, generate_insights


def main():
    parser = argparse.ArgumentParser(description="PhysioTrack - Player Movement Analysis")
    parser.add_argument("--video", required=True, help="Path to video file (max 3 min)")
    parser.add_argument("--sport", default="football", choices=["football", "volleyball", "badminton"])
    parser.add_argument("--output", default="physiotrack_result.json", help="Output JSON path")
    parser.add_argument("--sample-rate", type=int, default=3, help="Process every Nth frame")
    args = parser.parse_args()

    if not Path(args.video).exists():
        print(f"❌ Video not found: {args.video}")
        sys.exit(1)

    print(f"\n🎬 PhysioTrack | {args.sport.upper()} mode")
    print(f"   Video: {args.video}")
    print("─" * 50)

    # ── STEP 1: TRACKING ──
    print("📡 Running YOLO + ByteTrack detection...")
    t0 = time.time()

    def progress(pct, frame, processed):
        bar = "█" * (pct // 5) + "░" * (20 - pct // 5)
        print(f"\r   [{bar}] {pct}%  frame {frame}", end="", flush=True)

    tracking = run_tracking(
        args.video,
        sport=args.sport,
        sample_every=args.sample_rate,
        progress_callback=progress,
    )
    print(f"\n✅ Tracking done in {time.time()-t0:.1f}s")
    print(f"   Players: {len(tracking.player_tracks)} | Duration: {tracking.duration_seconds:.1f}s | FPS: {tracking.fps:.0f}")

    # ── STEP 2: LLM ROUTING ──
    print("\n🤖 LLM selecting analysis tools...")
    tracking_dict = {
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

    tool_descs = get_tool_descriptions()
    selected_tools = llm_select_tools(tracking_dict, tool_descs)
    print(f"   Selected: {selected_tools}")

    # ── STEP 3: ANALYSIS ──
    print("\n⚙️  Running analysis tools...")
    analysis = {}
    for tool_name in selected_tools:
        print(f"   Running {tool_name}...", end="", flush=True)
        result = run_tool(tool_name, tracking_dict)
        analysis[tool_name] = result
        print(" ✓")

    # ── STEP 4: INSIGHTS ──
    print("\n💡 Generating AI insights...")
    insights = generate_insights(analysis, args.sport)
    print("\n" + "─" * 50)
    print(insights)
    print("─" * 50)

    # ── SAVE ──
    payload = {
        "sport": tracking.sport,
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

    with open(args.output, "w") as f:
        json.dump(payload, f, indent=2)

    print(f"\n✅ Results saved to: {args.output}")
    print(f"   Launch web UI: python app.py")


if __name__ == "__main__":
    main()
