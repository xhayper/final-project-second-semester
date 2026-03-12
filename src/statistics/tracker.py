from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, cast
import json
import os


def _now_iso() -> str:
    return datetime.now().isoformat(timespec="seconds")


def _event_list() -> list[dict[str, Any]]:
    return []


def _int_map() -> dict[str, int]:
    return {}


@dataclass
class StatisticsTracker:
    item_spawn_count: int = 0
    item_despawn_count: int = 0
    machine_process_count: int = 0
    cash_earned: int = 0
    cash_spent: int = 0
    sold_item_counts: dict[str, int] = field(default_factory=_int_map)
    machine_process_breakdown: dict[str, int] = field(default_factory=_int_map)
    item_conversion_events: list[dict[str, Any]] = field(default_factory=_event_list)
    item_spawn_events: list[dict[str, Any]] = field(default_factory=_event_list)
    item_despawn_events: list[dict[str, Any]] = field(default_factory=_event_list)
    machine_process_events: list[dict[str, Any]] = field(default_factory=_event_list)
    cash_events: list[dict[str, Any]] = field(default_factory=_event_list)

    @property
    def efficiency(self) -> float:
        if self.item_spawn_count <= 0:
            return 0.0
        return (self.machine_process_count / self.item_spawn_count) * 100.0

    def reset(self):
        self.item_spawn_count = 0
        self.item_despawn_count = 0
        self.machine_process_count = 0
        self.cash_earned = 0
        self.cash_spent = 0
        self.sold_item_counts.clear()
        self.machine_process_breakdown.clear()
        self.item_conversion_events.clear()
        self.item_spawn_events.clear()
        self.item_despawn_events.clear()
        self.machine_process_events.clear()
        self.cash_events.clear()

    def record_item_spawn(self, item_type: str, source: str = "unknown"):
        self.item_spawn_count += 1
        self.item_spawn_events.append(
            {
                "timestamp": _now_iso(),
                "item_type": item_type,
                "source": source,
            }
        )

    def record_item_despawn(self, item_type: str, reason: str = "unknown"):
        self.item_despawn_count += 1
        self.item_despawn_events.append(
            {
                "timestamp": _now_iso(),
                "item_type": item_type,
                "reason": reason,
            }
        )

    def record_machine_process(
        self,
        machine_type: str,
        recipe_index: int,
        inputs: list[str],
        outputs: list[str],
    ):
        self.machine_process_count += 1
        if machine_type not in self.machine_process_breakdown:
            self.machine_process_breakdown[machine_type] = 0
        self.machine_process_breakdown[machine_type] += 1
        self.machine_process_events.append(
            {
                "timestamp": _now_iso(),
                "machine_type": machine_type,
                "recipe_index": recipe_index,
                "inputs": inputs,
                "outputs": outputs,
            }
        )

        self.item_conversion_events.append(
            {
                "timestamp": _now_iso(),
                "machine_type": machine_type,
                "recipe_index": recipe_index,
                "inputs": inputs,
                "outputs": outputs,
            }
        )

    def record_item_sold(self, item_type: str, amount: int = 1):
        if amount <= 0:
            return

        if item_type not in self.sold_item_counts:
            self.sold_item_counts[item_type] = 0
        self.sold_item_counts[item_type] += amount

    def record_cash_earned(self, amount: int, source: str = "unknown"):
        if amount <= 0:
            return

        self.cash_earned += amount
        self.cash_events.append(
            {
                "timestamp": _now_iso(),
                "kind": "earn",
                "amount": amount,
                "source": source,
            }
        )

    def record_cash_spent(self, amount: int, source: str = "unknown"):
        if amount <= 0:
            return

        self.cash_spent += amount
        self.cash_events.append(
            {
                "timestamp": _now_iso(),
                "kind": "spent",
                "amount": amount,
                "source": source,
            }
        )

    def to_dict(self) -> dict[str, Any]:
        return {
            "item_spawn_count": self.item_spawn_count,
            "item_despawn_count": self.item_despawn_count,
            "machine_process_count": self.machine_process_count,
            "cash_earned": self.cash_earned,
            "cash_spent": self.cash_spent,
            "sold_item_counts": self.sold_item_counts,
            "machine_process_breakdown": self.machine_process_breakdown,
            "efficiency": self.efficiency,
            "item_conversion_events": self.item_conversion_events,
            "item_spawn_events": self.item_spawn_events,
            "item_despawn_events": self.item_despawn_events,
            "machine_process_events": self.machine_process_events,
            "cash_events": self.cash_events,
            "analysis": self.analysis(),
        }

    def analysis(self) -> dict[str, Any]:
        spawn = max(0, self.item_spawn_count)
        despawn = max(0, self.item_despawn_count)
        process = max(0, self.machine_process_count)

        despawn_rate = (despawn / spawn) if spawn > 0 else 0.0
        conversion_rate = (process / spawn) if spawn > 0 else 0.0
        cash_delta = self.cash_earned - self.cash_spent

        bottlenecks: list[str] = []
        if spawn >= 20 and process <= 0:
            bottlenecks.append("No machine processing despite item throughput")
        if despawn_rate >= 0.3:
            bottlenecks.append(
                "High item despawn rate suggests transport/consumption bottleneck"
            )
        if self.cash_spent > (self.cash_earned * 1.5) and self.cash_spent > 0:
            bottlenecks.append(
                "Negative cash flow indicates production is underperforming"
            )

        if self.machine_process_breakdown:
            top_machine = max(
                self.machine_process_breakdown.items(),
                key=lambda x: x[1],
            )
            if process > 0 and (top_machine[1] / process) >= 0.8:
                bottlenecks.append(
                    f"Processing concentration is high on '{top_machine[0]}' ({top_machine[1]}/{process})"
                )

        efficiency_loss = max(0.0, 100.0 - (conversion_rate * 100.0))

        return {
            "despawn_rate": despawn_rate,
            "conversion_rate": conversion_rate,
            "cash_delta": cash_delta,
            "efficiency_loss": efficiency_loss,
            "bottlenecks": bottlenecks,
        }

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> StatisticsTracker:
        tracker = cls()
        tracker.item_spawn_count = int(payload.get("item_spawn_count", 0))
        tracker.item_despawn_count = int(payload.get("item_despawn_count", 0))
        tracker.machine_process_count = int(payload.get("machine_process_count", 0))
        tracker.cash_earned = int(payload.get("cash_earned", 0))
        tracker.cash_spent = int(payload.get("cash_spent", 0))
        tracker.sold_item_counts = dict(payload.get("sold_item_counts", {}))
        tracker.machine_process_breakdown = dict(
            payload.get("machine_process_breakdown", {})
        )
        tracker.item_conversion_events = list(payload.get("item_conversion_events", []))
        tracker.item_spawn_events = list(payload.get("item_spawn_events", []))
        tracker.item_despawn_events = list(payload.get("item_despawn_events", []))
        tracker.machine_process_events = list(payload.get("machine_process_events", []))
        tracker.cash_events = list(payload.get("cash_events", []))
        return tracker

    def load_file(self, path: str):
        if not os.path.exists(path):
            self.reset()
            return

        try:
            with open(path, "r", encoding="utf-8") as file:
                raw_payload: Any = json.load(file)
        except (json.JSONDecodeError, OSError):
            self.reset()
            return

        if not isinstance(raw_payload, dict):
            self.reset()
            return

        payload = cast(dict[str, Any], raw_payload)
        loaded = StatisticsTracker.from_dict(payload)
        self.item_spawn_count = loaded.item_spawn_count
        self.item_despawn_count = loaded.item_despawn_count
        self.machine_process_count = loaded.machine_process_count
        self.cash_earned = loaded.cash_earned
        self.cash_spent = loaded.cash_spent
        self.item_conversion_events = loaded.item_conversion_events
        self.item_spawn_events = loaded.item_spawn_events
        self.item_despawn_events = loaded.item_despawn_events
        self.machine_process_events = loaded.machine_process_events
        self.cash_events = loaded.cash_events

    def save_file(self, path: str):
        folder = os.path.dirname(path)
        if folder:
            os.makedirs(folder, exist_ok=True)

        with open(path, "w", encoding="utf-8") as file:
            json.dump(self.to_dict(), file, indent=2)
