from pathlib import Path
import json


class Statistics:
    DEFAULT_DATA = {
        "playtime": 0,
        "sessions_started": 0,
        "saves": 0,
        "loads": 0,
        "items_spawned": 0,
        "items_despawned": 0,
        "items_created_by_machines": 0,
        "items_inserted_into_machines": 0,
        "items_output_by_machines": 0,
        "items_sold": 0,
        "machines_placed": 0,
        "belts_placed": 0,
    }

    def __init__(self):
        self.data = {}

        self.load_data("statistics.json")
        self._ensure_defaults()

    def load_data(self, file: str):
        path = Path.cwd() / file

        if not path.exists():
            self.data = {}
            return

        with open(path, "r") as f:
            try:
                self.data = json.load(f)
            except json.decoder.JSONDecodeError:
                pass

    def save_data(self, file: str):
        path = Path.cwd() / file

        with open(path, "w") as f:
            json.dump(self.data, f)

    def clear(self):
        self.data = {}
        self._ensure_defaults()

    def _ensure_defaults(self):
        for key, value in self.DEFAULT_DATA.items():
            if key not in self.data:
                self.data[key] = value

    def get(self, key: str, default=None):
        if key not in self.data:
            return default

        return self.data[key]

    def set(self, key: str, value):
        self.data[key] = value

    def delete(self, key: str):
        del self.data[key]

    def increment(self, key: str, amount=1):
        value = self.get(key, 0)
        self.set(key, value + amount)

    def decrement(self, key: str, amount=1):
        value = self.get(key, 0)
        self.set(key, value - amount)
