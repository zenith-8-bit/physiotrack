"""
PhysioTrack - Core Tracking Engine
Extracts per-frame player positions from video using YOLOv8 + tracking
"""

import cv2
import json
import time
import numpy as np
from pathlib import Path
from ultralytics import YOLO
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional


@dataclass
class PlayerPosition:
    frame: int
    timestamp: float
    player_id: int
    x: float          # normalized 0-1
    y: float          # normalized 0-1
    x_px: int         # pixel coords
    y_px: int
    width: int
    height: int
    confidence: float
    speed: float = 0.0   # px/frame estimated
    zone: str = "unknown"


@dataclass
class TrackingResult:
    sport: str
    total_frames: int
    fps: float
    duration_seconds: float
    width: int
    height: int
    player_tracks: Dict[int, List[dict]]   # player_id -> list of positions
    frame_sample_rate: int
    raw_positions: List[dict]


MAX_DURATION_SEC = 180   # 3 min cap


def detect_sport_zones(sport: str, w: int, h: int) -> dict:
    """Return named court/field zones for the sport"""
    if sport == "football":
        return {
            "defense":     (0,        0,        w * 0.33, h),
            "midfield":    (w * 0.33, 0,        w * 0.66, h),
            "attack":      (w * 0.66, 0,        w,        h),
            "left_wing":   (0,        0,        w,        h * 0.25),
            "right_wing":  (0,        h * 0.75, w,        h),
            "center":      (0,        h * 0.25, w,        h * 0.75),
        }
    elif sport == "volleyball":
        return {
            "back_court":  (0,        0,        w,        h * 0.33),
            "mid_court":   (0,        h * 0.33, w,        h * 0.66),
            "front_court": (0,        h * 0.66, w,        h),
            "left_side":   (0,        0,        w * 0.33, h),
            "center":      (w * 0.33, 0,        w * 0.66, h),
            "right_side":  (w * 0.66, 0,        w,        h),
        }
    elif sport == "badminton":
        return {
            "back_court":  (0,        0,        w,        h * 0.25),
            "mid_court":   (0,        h * 0.25, w,        h * 0.75),
            "front_court": (0,        h * 0.75, w,        h),
            "left":        (0,        0,        w * 0.5,  h),
            "right":       (w * 0.5,  0,        w,        h),
        }
    else:
        return {}


def classify_zone(x_px, y_px, zones: dict) -> str:
    for name, (x0, y0, x1, y1) in zones.items():
        if x0 <= x_px <= x1 and y0 <= y_px <= y1:
            return name
    return "out_of_bounds"


def estimate_speed(prev_pos: Optional[dict], curr_pos: dict, fps: float) -> float:
    if prev_pos is None:
        return 0.0
    dx = curr_pos["x_px"] - prev_pos["x_px"]
    dy = curr_pos["y_px"] - prev_pos["y_px"]
    dist_px = np.sqrt(dx ** 2 + dy ** 2)
    return float(dist_px * fps)   # px/sec


def run_tracking(
    video_path: str,
    sport: str = "football",
    sample_every: int = 3,          # process every Nth frame for speed
    progress_callback=None
) -> TrackingResult:
    """
    Main tracking pipeline.
    Returns structured TrackingResult with all player positions.
    """
    model = YOLO("yolov8n.pt")   # auto-downloads on first run

    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        raise ValueError(f"Cannot open video: {video_path}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 30.0
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    # Cap at 3 min
    max_frames = int(min(total_frames, MAX_DURATION_SEC * fps))
    duration = max_frames / fps

    zones = detect_sport_zones(sport, w, h)

    raw_positions: List[dict] = []
    player_tracks: Dict[int, List[dict]] = {}
    prev_by_id: Dict[int, dict] = {}

    frame_idx = 0
    processed = 0

    while frame_idx < max_frames:
        ret, frame = cap.read()
        if not ret:
            break

        if frame_idx % sample_every == 0:
            timestamp = frame_idx / fps

            # Run YOLO with built-in ByteTrack
            results = model.track(
                frame,
                persist=True,
                classes=[0],          # person only
                conf=0.35,
                iou=0.5,
                tracker="bytetrack.yaml",
                verbose=False,
            )

            if results and results[0].boxes is not None:
                boxes = results[0].boxes
                for box in boxes:
                    if box.id is None:
                        continue
                    pid = int(box.id.item())
                    x1, y1, x2, y2 = box.xyxy[0].tolist()
                    cx = int((x1 + x2) / 2)
                    cy = int((y1 + y2) / 2)
                    bw = int(x2 - x1)
                    bh = int(y2 - y1)
                    conf = float(box.conf.item())

                    pos = {
                        "frame": frame_idx,
                        "timestamp": round(timestamp, 3),
                        "player_id": pid,
                        "x": round(cx / w, 4),
                        "y": round(cy / h, 4),
                        "x_px": cx,
                        "y_px": cy,
                        "width": bw,
                        "height": bh,
                        "confidence": round(conf, 3),
                        "speed": round(estimate_speed(prev_by_id.get(pid), {"x_px": cx, "y_px": cy}, fps / sample_every), 2),
                        "zone": classify_zone(cx, cy, zones),
                    }

                    raw_positions.append(pos)
                    if pid not in player_tracks:
                        player_tracks[pid] = []
                    player_tracks[pid].append(pos)
                    prev_by_id[pid] = pos

            processed += 1
            if progress_callback:
                pct = int((frame_idx / max_frames) * 100)
                progress_callback(pct, frame_idx, processed)

        frame_idx += 1

    cap.release()

    return TrackingResult(
        sport=sport,
        total_frames=max_frames,
        fps=fps,
        duration_seconds=round(duration, 2),
        width=w,
        height=h,
        player_tracks=player_tracks,
        frame_sample_rate=sample_every,
        raw_positions=raw_positions,
    )
