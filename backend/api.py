from pathlib import Path
from dataclasses import asdict
from typing import Any
import sys
from io import BytesIO
import json
import tempfile

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from fastapi.responses import Response

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from gunite_calculator import GuniteInput, BeamObstruction, calculate, order_rows, result_table  # noqa: E402
import catalog  # noqa: E402
import database  # noqa: E402
import project_io  # noqa: E402
import drawing  # noqa: E402
from pdf_report import create_project_pdf  # noqa: E402

app = FastAPI(title="GUNITE Engineering API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

class BeamModel(BaseModel):
    enabled: bool = False
    side: str = "Καμία"
    interrupted_bars: int = 0
    beam_bottom_m: float = 1.20
    beam_height_m: float = 0.50
    lower_piece_m: float = 3.00
    upper_piece_m: float = 2.00

class CalcModel(BaseModel):
    name: str = "Νέο στοιχείο"
    x1b: float = 45.0
    x2b: float = 45.0
    y1b: float = 35.0
    y2b: float = 35.0
    fd_mm: float = 25.0
    corner_fd_mm: float | None = None
    x_side_fd_mm: float | None = None
    y_side_fd_mm: float | None = None
    fs_mm: float = 10.0
    spacing_mm: int = 100
    a1_cm: float = 1.0
    a2_cm: float = 0.5
    tgun_cm: float = 7.5
    dh_cm: float = 5.0
    floor_height_m: float = 3.46
    waiting_m: float = 1.0
    nx: int = 3
    ny: int = 4
    overlap_factor: float = 80.0
    development_option: str = "1a"
    beam: BeamModel | None = Field(default_factory=BeamModel)


class ProjectModel(BaseModel):
    name: str = "Νέο έργο"
    floors: list[dict[str, Any]] = Field(default_factory=list)
    elements: list[dict[str, Any]] = Field(default_factory=list)


class ProjectSaveModel(ProjectModel):
    id: int | None = None


def make_input(m: CalcModel) -> GuniteInput:
    return GuniteInput(
        name=m.name, x1b=m.x1b, x2b=m.x2b, y1b=m.y1b, y2b=m.y2b,
        fd_mm=m.fd_mm, corner_fd_mm=m.corner_fd_mm, x_side_fd_mm=m.x_side_fd_mm,
        y_side_fd_mm=m.y_side_fd_mm, fs_mm=m.fs_mm, spacing_mm=m.spacing_mm,
        a1_cm=m.a1_cm, a2_cm=m.a2_cm, tgun_cm=m.tgun_cm, dh_cm=m.dh_cm,
        floor_height_m=m.floor_height_m, waiting_m=m.waiting_m, nx=m.nx, ny=m.ny,
        overlap_factor=m.overlap_factor, development_option=m.development_option,
        beam=None if m.beam is None else BeamObstruction(**m.beam.model_dump()),
    )


def calculate_payload(model: CalcModel) -> dict[str, Any]:
    inp = make_input(model)
    res = calculate(inp)
    return {
        "input": model.model_dump(),
        "result": asdict(res),
        "result_table": result_table(inp, res),
        "order_rows": order_rows(inp, res),
    }


def raw_element_record(record: dict[str, Any]) -> dict[str, Any]:
    """Accept both raw saved elements and calculated API response elements."""
    if isinstance(record.get("input"), dict):
        raw = dict(record["input"])
        for key in ("floor_name", "study_dimensions", "remarks", "designer_remarks", "length_cm", "width_cm"):
            if key in record:
                raw[key] = record[key]
        return raw
    return record


def storage_elements(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Convert API records to the legacy database's {input, result} shape."""
    stored = []
    for record in records:
        raw = raw_element_record(record)
        model = CalcModel.model_validate(raw)
        calculated = calculate_payload(model)
        stored.append({
            "input": make_input(model),
            "result": type("StoredResult", (), {"case": calculated["result"]["case"]})(),
            "order_rows": calculated["order_rows"],
            "floor_name": raw.get("floor_name", "Στάθμη 1"),
            "study_dimensions": raw.get("study_dimensions", ""),
            "remarks": raw.get("remarks", ""),
            "designer_remarks": raw.get("designer_remarks", ""),
            "length_cm": raw.get("length_cm", model.x1b + model.x2b),
            "width_cm": raw.get("width_cm", model.y1b + model.y2b),
        })
    return stored


def project_elements_payload(project: dict[str, Any]) -> list[dict[str, Any]]:
    output = []
    for record in project.get("elements", []):
        record = raw_element_record(record)
        model = CalcModel.model_validate(record)
        calculated = calculate_payload(model)
        calculated["floor_name"] = record.get("floor_name", "Στάθμη 1")
        calculated["study_dimensions"] = record.get("study_dimensions", "")
        calculated["remarks"] = record.get("remarks", "")
        calculated["designer_remarks"] = record.get("designer_remarks", "")
        calculated["length_cm"] = record.get("length_cm", model.x1b + model.x2b)
        calculated["width_cm"] = record.get("width_cm", model.y1b + model.y2b)
        output.append(calculated)
    return output


def project_tables(project: dict[str, Any], calculated: list[dict[str, Any]]):
    rows = []
    order = []
    for index, item in enumerate(calculated, start=1):
        model = CalcModel.model_validate(item["input"])
        result = item["result"]
        rows.append({
            "α/α": index, "Στοιχείο": model.name, "Στάθμη": item.get("floor_name", "—"),
            "Περίπτωση": result["case"],
            "Gunite (m³)": result["gunite_volume_m3"],
            "Διατομή gunite": f'{result["gunite_width_m"]*100:.1f} × {result["gunite_height_m"]*100:.1f} cm',
        })
        order.extend(item["order_rows"])
    elements_df = pd.DataFrame(rows)
    order_df = pd.DataFrame(order)
    if order_df.empty:
        summary_df = pd.DataFrame()
    else:
        summary_df = (order_df.groupby(["Τύπος", "Περιγραφή", "Μήκος (m)"], as_index=False)
                      .agg({"Τεμάχια": "sum", "Σύνολο kg": "sum"}))
    return elements_df, order_df, summary_df

@app.get("/api/health")
def health():
    return {"ok": True, "catalog_source": catalog.CATALOG_SOURCE, "catalog_count": len(catalog.CATALOG)}

@app.get("/api/catalog")
def get_catalog():
    return {
        "diameters": catalog.available_diameters(),
        "spacings": catalog.available_spacings(),
        "items": [asdict(x) for x in catalog.CATALOG],
    }

@app.post("/api/calculate")
def calculate_api(model: CalcModel):
    try:
        return calculate_payload(model)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/projects")
def projects_api():
    return {"projects": database.list_projects()}


@app.get("/api/projects/{project_id}")
def project_api(project_id: int):
    project = database.load_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Το έργο δεν βρέθηκε.")
    try:
        return {**project, "elements": project_elements_payload(project)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/projects")
def save_project_api(model: ProjectSaveModel):
    try:
        raw_elements = storage_elements(model.elements)
        project_id = database.save_project(
            model.name, raw_elements, project_id=model.id, floors=model.floors
        )
        project = database.load_project(project_id)
        return {**project, "elements": project_elements_payload(project)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.delete("/api/projects/{project_id}")
def delete_project_api(project_id: int):
    database.delete_project(project_id)
    return {"ok": True}


@app.post("/api/projects/import")
def import_project_api(model: ProjectModel):
    try:
        project_id = database.save_project(model.name, storage_elements(model.elements), floors=model.floors)
        project = database.load_project(project_id)
        return {**project, "elements": project_elements_payload(project)}
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.get("/api/projects/{project_id}/export")
def export_project_api(project_id: int):
    with tempfile.NamedTemporaryFile(suffix=".gunite", delete=False) as tmp:
        target = Path(tmp.name)
    try:
        project_io.export_project(project_id, target)
        data = target.read_bytes()
    except Exception as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    finally:
        target.unlink(missing_ok=True)
    return Response(data, media_type="application/json", headers={"Content-Disposition": 'attachment; filename="gunite-project.gunite"'})


@app.post("/api/project/report/{report_type}")
def project_report_api(report_type: str, model: ProjectModel):
    """Generate the same project-level Excel/PDF outputs as the legacy app."""
    try:
        calculated = project_elements_payload(model.model_dump())
        elements_df, order_df, summary_df = project_tables(model.model_dump(), calculated)
        if report_type == "excel":
            output = BytesIO()
            with pd.ExcelWriter(output, engine="openpyxl") as writer:
                elements_df.to_excel(writer, sheet_name="Στοιχεία Έργου", index=False)
                order_df.to_excel(writer, sheet_name="Αναλυτική Παραγγελία", index=False)
                summary_df.to_excel(writer, sheet_name="Συγκεντρωτική", index=False)
            return Response(output.getvalue(), media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", headers={"Content-Disposition": 'attachment; filename="gunite-project.xlsx"'})
        if report_type == "pdf":
            pdf = create_project_pdf(elements_df, order_df, summary_df)
            return Response(pdf, media_type="application/pdf", headers={"Content-Disposition": 'attachment; filename="gunite-project.pdf"'})
        raise HTTPException(status_code=400, detail="Άγνωστος τύπος αναφοράς.")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc


@app.post("/api/drawing/{drawing_type}")
def drawing_api(drawing_type: str, model: CalcModel):
    try:
        inp = make_input(model)
        res = calculate(inp)
        functions = {
            "section": drawing.draw_column_section,
            "jacket": drawing.draw_jacket_developments,
            "vertical": drawing.draw_vertical_reinforcement,
            "technical": drawing.draw_technical_sheet,
        }
        if drawing_type not in functions:
            raise HTTPException(status_code=400, detail="Άγνωστος τύπος σχεδίου.")
        fig = functions[drawing_type](inp, res, size="Μεγάλο")
        image = BytesIO()
        fig.savefig(image, format="png", dpi=180, bbox_inches="tight", facecolor="white")
        import matplotlib.pyplot as plt
        plt.close(fig)
        return Response(image.getvalue(), media_type="image/png")
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
