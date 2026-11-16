"""Configuración compartida entre usuarios: el umbral de alerta que fija Anna.

Se guarda en data/configuracion.json, un valor por archivo de datos (identificado por su SHA-256),
para que Laura, Armando y Anna usen el mismo umbral aunque cambien de usuario o se reinicie la app.
"""
from __future__ import annotations

import json
import threading
from pathlib import Path

FILE = Path(__file__).resolve().parents[1] / "data" / "configuracion.json"
_lock = threading.Lock()


def _read() -> dict:
    try:
        return json.loads(FILE.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def get_threshold(sha: str) -> dict | None:
    """{'umbral': 0.29, 'por': 'anna', 'cuando': '...'} o None si nadie lo ha cambiado."""
    return _read().get("umbral", {}).get(sha)


def set_threshold(sha: str, value: float, user: str, when: str) -> None:
    value = round(min(0.9, max(0.05, float(value))), 2)
    with _lock:
        data = _read()
        data.setdefault("umbral", {})[sha] = {"umbral": value, "por": user, "cuando": when}
        FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def clear_threshold(sha: str) -> None:
    with _lock:
        data = _read()
        data.get("umbral", {}).pop(sha, None)
        FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
