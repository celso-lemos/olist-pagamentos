"""Leitura dos indicadores publicados, sem acesso ao banco ou dados raw."""

import json
from pathlib import Path


DATA = Path(__file__).resolve().parent / "data" / "published" / "dashboard.json"


def load_data():
    return json.loads(DATA.read_text(encoding="utf-8"))
