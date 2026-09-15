from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

import database

PACKAGE_VERSION = 1


def export_project(project_id: int, target: Path) -> Path:
    project = database.load_project(project_id)
    if not project:
        raise ValueError("Το έργο δεν βρέθηκε.")
    payload = {
        "format": "GUNITE_PROJECT",
        "version": PACKAGE_VERSION,
        "exported_at": datetime.now().isoformat(timespec="seconds"),
        "project": project,
    }
    target = Path(target)
    target.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return target


def import_project(source: Path) -> int:
    source = Path(source)
    payload = json.loads(source.read_text(encoding="utf-8"))
    if payload.get("format") != "GUNITE_PROJECT":
        raise ValueError("Το αρχείο δεν είναι αρχείο έργου GUNITE.")
    project = payload.get("project") or {}
    name = str(project.get("name") or source.stem)
    elements = project.get("elements") or []
    return database.save_project(name, elements, project_id=None, floors=project.get("floors") or [])
