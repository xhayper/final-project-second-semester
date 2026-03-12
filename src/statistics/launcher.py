from __future__ import annotations

from typing import Any
import subprocess
import tempfile
import json
import sys
import os


def _normalize_statistics_path(path: str) -> str:
    if path.endswith(".stats.json"):
        return path

    if path.endswith(".data"):
        return f"{path[:-5]}.stats.json"

    return path


def launch_statistics_window(statistics_file: str):
    path = _normalize_statistics_path(statistics_file)

    launch_path = path
    if not os.path.exists(path):
        default_payload: dict[str, Any] = {
            "item_spawn_count": 0,
            "item_despawn_count": 0,
            "machine_process_count": 0,
            "cash_earned": 0,
            "cash_spent": 0,
            "efficiency": 0.0,
            "sold_item_counts": {},
            "machine_process_breakdown": {},
            "item_conversion_events": [],
            "item_spawn_events": [],
            "item_despawn_events": [],
            "machine_process_events": [],
            "cash_events": [],
            "analysis": {
                "despawn_rate": 0.0,
                "conversion_rate": 0.0,
                "cash_delta": 0,
                "efficiency_loss": 100.0,
                "bottlenecks": ["No statistics recorded for this slot yet"],
            },
        }

        with tempfile.NamedTemporaryFile(
            mode="w",
            suffix=".stats.json",
            prefix="empty_slot_",
            delete=False,
            encoding="utf-8",
        ) as tmp:
            json.dump(default_payload, tmp)
            launch_path = tmp.name

    try:
        subprocess.Popen([sys.executable, "-m", "src.statistics.viewer", launch_path])
    except OSError:
        return False

    return True
