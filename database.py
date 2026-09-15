from __future__ import annotations

import json
import sqlite3
from datetime import datetime
from pathlib import Path
import os
from typing import Any, Dict, List, Optional

def _data_dir() -> Path:
    # User data must survive application upgrades/reinstalls.
    base = os.environ.get("LOCALAPPDATA")
    if base:
        path = Path(base) / "GUNITE Calculator"
    else:
        path = Path.home() / ".gunite_calculator"
    path.mkdir(parents=True, exist_ok=True)
    return path


DB_PATH = _data_dir() / "gunite_projects.db"


def connect(path: Path = DB_PATH) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con


def init_db(path: Path = DB_PATH) -> None:
    with connect(path) as con:
        con.executescript(
            """
            CREATE TABLE IF NOT EXISTS projects (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                floors_json TEXT NOT NULL DEFAULT '[]'
            );

            CREATE TABLE IF NOT EXISTS elements (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id INTEGER NOT NULL,
                position INTEGER NOT NULL,
                data_json TEXT NOT NULL,
                FOREIGN KEY(project_id) REFERENCES projects(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_elements_project
                ON elements(project_id, position);
            """
        )
        columns = {row[1] for row in con.execute("PRAGMA table_info(projects)").fetchall()}
        if "floors_json" not in columns:
            con.execute("ALTER TABLE projects ADD COLUMN floors_json TEXT NOT NULL DEFAULT '[]'")


def list_projects(path: Path = DB_PATH) -> List[Dict[str, Any]]:
    init_db(path)
    with connect(path) as con:
        rows = con.execute(
            "SELECT id, name, created_at, updated_at FROM projects ORDER BY updated_at DESC, id DESC"
        ).fetchall()
    return [dict(r) for r in rows]


def save_project(name: str, elements: List[Dict[str, Any]], project_id: Optional[int] = None,
                 path: Path = DB_PATH, floors: Optional[List[Dict[str, Any]]] = None) -> int:
    init_db(path)
    now = datetime.now().isoformat(timespec="seconds")
    payloads = [serialize_element(e) for e in elements]
    floors_payload = floors or []
    floors_json = json.dumps(floors_payload, ensure_ascii=False)
    with connect(path) as con:
        if project_id is None:
            cur = con.execute(
                "INSERT INTO projects(name, created_at, updated_at, floors_json) VALUES(?,?,?,?)",
                (name.strip() or "Νέο έργο", now, now, floors_json),
            )
            project_id = int(cur.lastrowid)
        else:
            con.execute(
                "UPDATE projects SET name=?, updated_at=?, floors_json=? WHERE id=?",
                (name.strip() or "Νέο έργο", now, floors_json, project_id),
            )
            con.execute("DELETE FROM elements WHERE project_id=?", (project_id,))

        for pos, payload in enumerate(payloads, start=1):
            con.execute(
                "INSERT INTO elements(project_id, position, data_json) VALUES(?,?,?)",
                (project_id, pos, json.dumps(payload, ensure_ascii=False)),
            )
    return project_id


def load_project(project_id: int, path: Path = DB_PATH) -> Optional[Dict[str, Any]]:
    init_db(path)
    with connect(path) as con:
        project = con.execute("SELECT * FROM projects WHERE id=?", (project_id,)).fetchone()
        if project is None:
            return None
        rows = con.execute(
            "SELECT data_json FROM elements WHERE project_id=? ORDER BY position, id", (project_id,)
        ).fetchall()
    return {
        "id": int(project["id"]),
        "name": project["name"],
        "created_at": project["created_at"],
        "updated_at": project["updated_at"],
        "floors": json.loads(project["floors_json"] or "[]"),
        "elements": [json.loads(r["data_json"]) for r in rows],
    }


def delete_project(project_id: int, path: Path = DB_PATH) -> None:
    init_db(path)
    with connect(path) as con:
        con.execute("DELETE FROM projects WHERE id=?", (project_id,))


def serialize_element(item: Dict[str, Any]) -> Dict[str, Any]:
    inp = item["input"]
    res = item.get("result")
    case = getattr(res, "case", None) or item.get("case") or "4πλευρος μανδύας"
    return {
        "case": case,
        "floor_name": item.get("floor_name", "Στάθμη 1"),
        "study_dimensions": item.get("study_dimensions", ""),
        "remarks": item.get("remarks", ""),
        "designer_remarks": item.get("designer_remarks", ""),
        "length_cm": item.get("length_cm", inp.x1b + inp.x2b),
        "width_cm": item.get("width_cm", inp.y1b + inp.y2b),
        "name": inp.name,
        "x1b": inp.x1b, "x2b": inp.x2b, "y1b": inp.y1b, "y2b": inp.y2b,
        "fd_mm": inp.fd_mm,
        "corner_fd_mm": inp.corner_fd_mm, "x_side_fd_mm": inp.x_side_fd_mm, "y_side_fd_mm": inp.y_side_fd_mm,
        "fs_mm": inp.fs_mm, "spacing_mm": inp.spacing_mm,
        "a1_cm": inp.a1_cm, "a2_cm": inp.a2_cm, "tgun_cm": inp.tgun_cm, "dh_cm": inp.dh_cm,
        "floor_height_m": inp.floor_height_m, "waiting_m": inp.waiting_m,
        "nx": inp.nx, "ny": inp.ny, "overlap_factor": inp.overlap_factor,
        "development_option": getattr(inp, "development_option", "1a"),
        "beam": None if inp.beam is None else inp.beam.__dict__,
    }
