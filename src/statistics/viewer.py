from __future__ import annotations

from typing import Any, cast
import json
import sys
import os


def _to_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _to_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_dict(value: Any) -> dict[str, Any]:
    if not isinstance(value, dict):
        return {}
    return cast(dict[str, Any], value)


def _as_event_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []

    raw_list = cast(list[Any], value)
    out: list[dict[str, Any]] = []
    for item in raw_list:
        if isinstance(item, dict):
            out.append(cast(dict[str, Any], item))
    return out


def _sorted_count_pairs(value: Any) -> list[tuple[str, int]]:
    mapping = _as_dict(value)
    pairs: list[tuple[str, int]] = []
    for key, raw_count in mapping.items():
        pairs.append((str(key), _to_int(raw_count)))
    pairs.sort(key=lambda pair: pair[1], reverse=True)
    return pairs


def _ensure_min_points(series: list[float], minimum: int = 100) -> list[float]:
    if len(series) >= minimum:
        return series

    if len(series) == 0:
        return [0.0 for _ in range(minimum)]

    if len(series) == 1:
        return [series[0] for _ in range(minimum)]

    out: list[float] = []
    max_idx = len(series) - 1
    for i in range(minimum):
        src_pos = (i / (minimum - 1)) * max_idx
        left = int(src_pos)
        right = min(max_idx, left + 1)
        if left == right:
            out.append(series[left])
            continue
        alpha = src_pos - left
        out.append((series[left] * (1.0 - alpha)) + (series[right] * alpha))
    return out


def _build_count_series(
    events: list[dict[str, Any]], minimum: int = 100
) -> list[float]:
    values: list[float] = []
    counter = 0.0
    for _ in events:
        counter += 1.0
        values.append(counter)
    return _ensure_min_points(values, minimum=minimum)


def _build_cash_series(
    cash_events: list[dict[str, Any]], minimum: int = 100
) -> list[float]:
    earned = 0.0
    spent = 0.0
    net_values: list[float] = []
    for evt in cash_events:
        amount = _to_float(evt.get("amount", 0.0))
        if str(evt.get("kind", "")) == "earn":
            earned += amount
        else:
            spent += amount
        net_values.append(earned - spent)
    return _ensure_min_points(net_values, minimum=minimum)


def _detect_bottleneck(payload: dict[str, Any]) -> list[str]:
    analysis = _as_dict(payload.get("analysis", {}))

    bottlenecks = analysis.get("bottlenecks", [])
    if isinstance(bottlenecks, list):
        values = cast(list[Any], bottlenecks)
        return [str(x) for x in values]
    return []


def _render_window(payload: dict[str, Any]):
    import tkinter as tk

    from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
    from matplotlib.figure import Figure

    root = tk.Tk()
    root.title("Game Statistics")
    root.geometry("1100x760")

    metrics = tk.Frame(root)
    metrics.pack(fill="x", padx=10, pady=(10, 5))

    efficiency = _to_float(payload.get("efficiency", 0.0))
    labels = [
        f"Item Spawn: {_to_int(payload.get('item_spawn_count', 0))}",
        f"Item Despawn: {_to_int(payload.get('item_despawn_count', 0))}",
        f"Machine Process: {_to_int(payload.get('machine_process_count', 0))}",
        f"Cash Earned: {_to_int(payload.get('cash_earned', 0))}",
        f"Cash Spent: {_to_int(payload.get('cash_spent', 0))}",
        f"Efficiency: {efficiency:.2f}%",
    ]
    tk.Label(metrics, text=" | ".join(labels), anchor="w", justify="left").pack(
        fill="x"
    )

    fig = Figure(figsize=(11, 6.2), dpi=100)
    ax_count_line: Any = fig.add_subplot(221)
    ax_cash_line: Any = fig.add_subplot(222)
    ax_machine_bar: Any = fig.add_subplot(223)
    ax_items_bar: Any = fig.add_subplot(224)

    spawn_series = _build_count_series(
        _as_event_list(payload.get("item_spawn_events", [])), minimum=100
    )
    despawn_series = _build_count_series(
        _as_event_list(payload.get("item_despawn_events", [])), minimum=100
    )
    process_series = _build_count_series(
        _as_event_list(payload.get("machine_process_events", [])), minimum=100
    )
    cash_net_series = _build_cash_series(
        _as_event_list(payload.get("cash_events", [])), minimum=100
    )

    ax_count_line.plot(
        range(len(spawn_series)), spawn_series, label="spawn", color="#4caf50"
    )

    ax_count_line.plot(
        range(len(despawn_series)), despawn_series, label="despawn", color="#f44336"
    )

    ax_count_line.plot(
        range(len(process_series)), process_series, label="process", color="#2196f3"
    )
    ax_count_line.set_title("Event Trends")
    ax_count_line.legend(loc="upper left", fontsize=8)

    ax_cash_line.plot(
        list(range(len(cash_net_series))),
        cash_net_series,
        label="net cash",
        color="#ff9800",
    )
    ax_cash_line.set_title("Net Cash Trend (100+ points)")
    ax_cash_line.legend(loc="upper left", fontsize=8)

    machine_pairs = _sorted_count_pairs(payload.get("machine_process_breakdown", {}))
    machine_labels = [k for k, _ in machine_pairs[:8]]
    machine_values = [v for _, v in machine_pairs[:8]]
    if len(machine_labels) == 0:
        machine_labels = ["none"]
        machine_values = [0]
    ax_machine_bar.bar(machine_labels, machine_values, color="#03a9f4")
    ax_machine_bar.set_title("Per-Machine Process Breakdown")
    ax_machine_bar.tick_params(axis="x", rotation=25)

    sold_pairs = _sorted_count_pairs(payload.get("sold_item_counts", {}))
    sold_labels = [k for k, _ in sold_pairs[:8]]
    sold_values = [v for _, v in sold_pairs[:8]]
    if len(sold_labels) == 0:
        sold_labels = ["none"]
        sold_values = [0]
    ax_items_bar.bar(sold_labels, sold_values, color="#8bc34a")
    ax_items_bar.set_title("Top Sold Item Types")
    ax_items_bar.tick_params(axis="x", rotation=25)

    fig.tight_layout()

    canvas = FigureCanvasTkAgg(fig, master=root)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="x", padx=10, pady=5)

    text = tk.Text(root, wrap="word", height=16)
    text.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    text.insert("end", "Bottleneck / Efficiency Analysis\n")
    text.insert("end", "=" * 34 + "\n")
    analysis = _as_dict(payload.get("analysis", {}))
    if len(analysis) > 0:
        text.insert(
            "end",
            f"despawn_rate={_to_float(analysis.get('despawn_rate', 0.0)):.2%}\n",
        )
        text.insert(
            "end",
            f"conversion_rate={_to_float(analysis.get('conversion_rate', 0.0)):.2%}\n",
        )
        text.insert(
            "end",
            f"efficiency_loss={_to_float(analysis.get('efficiency_loss', 0.0)):.2f}%\n",
        )
        text.insert(
            "end",
            f"cash_delta={_to_int(analysis.get('cash_delta', 0))}\n",
        )

    bottlenecks = _detect_bottleneck(payload)
    if len(bottlenecks) == 0:
        text.insert("end", "No major bottlenecks detected.\n")
    else:
        for item in bottlenecks:
            text.insert("end", f"- {item}\n")

    text.insert("end", "\nRecent Conversion Events\n")
    text.insert("end", "=" * 28 + "\n")
    for event in _as_event_list(payload.get("item_conversion_events", []))[-25:]:
        text.insert(
            "end",
            f"[{event.get('timestamp', '')}] {event.get('machine_type', '')} "
            f"in={event.get('inputs', [])} out={event.get('outputs', [])}\n",
        )

    text.insert("end", "\nRecent Cash Events\n")
    text.insert("end", "=" * 20 + "\n")
    for event in _as_event_list(payload.get("cash_events", []))[-25:]:
        text.insert(
            "end",
            f"[{event.get('timestamp', '')}] {event.get('kind', '')} "
            f"{event.get('amount', 0)} ({event.get('source', '')})\n",
        )

    text.configure(state="disabled")

    root.mainloop()


def _main():
    if len(sys.argv) < 2:
        return

    path = sys.argv[1]
    if not os.path.exists(path):
        return

    try:
        with open(path, "r", encoding="utf-8") as file:
            raw_payload: Any = json.load(file)
    except (json.JSONDecodeError, OSError):
        return

    if not isinstance(raw_payload, dict):
        return

    payload = cast(dict[str, Any], raw_payload)
    _render_window(payload)


if __name__ == "__main__":
    _main()
