import json
import os
from src.config import settings

class ApprovalStore:
    def __init__(self, path: str | None = None):
        self.path = path or settings.approval_store_path
        if not os.path.exists(self.path):
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def _read(self):
        with open(self.path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _write(self, data):
        with open(self.path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def save_pending(self, record: dict):
        data = self._read()
        data.append(record)
        self._write(data)
        return record

    def list_all(self):
        return self._read()

    def latest_for_sku(self, sku: str):
        all_records = self._read()
        for item in reversed(all_records):
            if item.get("sku") == sku:
                return item
        return None
