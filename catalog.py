from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Tuple
import re

import pandas as pd

try:
    from .docx_loader import extract_mandyes
except Exception:
    try:
        from docx_loader import extract_mandyes
    except Exception:
        extract_mandyes = None


@dataclass
class CatalogItem:
    diameter_mm: int
    spacing_mm: int
    development_m: float
    height_m: float
    weight_kg: float
    name: str


DEFAULT_CATALOG_PATH = Path(__file__).parent / "προτυπο με μανδυες_.xlsx"
DOCX_CATALOG_PATH = Path(__file__).parent / "GUNITE_Logic.docx"


def _parse_number(value) -> float:
    if pd.isna(value):
        raise ValueError("Missing numeric value")
    if isinstance(value, str):
        text = value.strip().replace(",", ".")
        if text == "":
            raise ValueError("Empty numeric string")
        return float(text)
    return float(value)


def _parse_catalog_name(name: str) -> Tuple[int, int, float]:
    if not isinstance(name, str):
        raise ValueError("Invalid catalog name")
    text = name.strip().replace("Φ", "").replace("φ", "")
    match = re.match(r"^\s*(\d+(?:[.,]\d*)?)\s*/\s*(\d+)\s*/\s*(\d+)\s*$", text)
    if not match:
        raise ValueError(f"Cannot parse catalog name: {name}")
    development, diameter, spacing = match.groups()
    return int(diameter), int(spacing), float(development.replace(",", ".")) / 100.0


def _canonical_name(development_m: float, diameter_mm: int, spacing_mm: int) -> str:
    value = development_m * 100.0
    if abs(value - round(value)) < 1e-6:
        dev = str(int(round(value)))
    else:
        dev = f"{value:.2f}".rstrip("0").rstrip(".")
    return f"{dev}/{diameter_mm}/{spacing_mm}"


def _default_catalog_items() -> List[CatalogItem]:
    """Never invent catalog products: packaged DOCX/Excel sources are authoritative."""
    return []


CATALOG: List[CatalogItem] = []
CATALOG_SOURCE: str = "source unavailable"


def _rows_to_items(rows: List[dict]) -> List[CatalogItem]:
    items: List[CatalogItem] = []
    for r in rows:
        name = str(r.get("Ονομασία", "")).strip()
        if not name or name.lower() == "nan":
            continue
        try:
            diameter_mm, spacing_mm, name_development_m = _parse_catalog_name(name)
            development_m = _parse_number(r.get("Αναπτυγμα (m)"))
            height_m = _parse_number(r.get("Ύψος (m)"))
            weight_kg = _parse_number(r.get("Βαρος (kg)"))
        except Exception:
            continue

        # The DOCX group is authoritative for Φ and spacing. Correct known
        # row-name typos while preserving the actual development/weight data.
        section = r.get("_section")
        if section:
            diameter_mm, spacing_mm = section
            # Development column is authoritative over the text label.
            name = _canonical_name(development_m, diameter_mm, spacing_mm)
        elif development_m <= 0:
            development_m = name_development_m

        items.append(CatalogItem(
            diameter_mm=diameter_mm,
            spacing_mm=spacing_mm,
            development_m=round(development_m, 3),
            height_m=round(height_m, 3),
            weight_kg=round(weight_kg, 3),
            name=name,
        ))

    # De-duplicate identical catalog records.
    unique = {}
    for item in items:
        key = (item.diameter_mm, item.spacing_mm, item.development_m)
        unique[key] = item
    return sorted(unique.values(), key=lambda x: (x.diameter_mm, x.spacing_mm, x.development_m))


def load_catalog_items(file_path: Optional[Path] = None) -> List[CatalogItem]:
    global CATALOG_SOURCE
    file_path = Path(file_path) if file_path is not None else DEFAULT_CATALOG_PATH

    if DOCX_CATALOG_PATH.exists() and extract_mandyes is not None:
        try:
            items = _rows_to_items(extract_mandyes(DOCX_CATALOG_PATH))
            if items:
                CATALOG_SOURCE = f"docx ({DOCX_CATALOG_PATH.name})"
                return items
        except Exception:
            pass

    if file_path.exists():
        try:
            df = pd.read_excel(file_path, sheet_name="ΜΑΝΔΥΕΣ", engine="openpyxl")
            rows = []
            for _, row in df.iterrows():
                rows.append({
                    "Ονομασία": row.get("Ονομασία"),
                    "Αναπτυγμα (m)": row.get("Αναπτυγμα (m)"),
                    "Ύψος (m)": row.get("Ύψος (m)"),
                    "Βαρος (kg)": row.get("Βαρος (kg)"),
                })
            items = _rows_to_items(rows)
            if items:
                CATALOG_SOURCE = f"excel ({file_path.name})"
                return items
        except Exception:
            pass

    CATALOG_SOURCE = "source unavailable"
    return _default_catalog_items()


CATALOG = load_catalog_items()


def available_diameters() -> List[int]:
    return sorted({item.diameter_mm for item in CATALOG})


def available_spacings(diameter_mm: Optional[int] = None) -> List[int]:
    items = CATALOG if diameter_mm is None else [i for i in CATALOG if i.diameter_mm == int(diameter_mm)]
    return sorted({item.spacing_mm for item in items})


def available_catalog_names() -> List[str]:
    return [item.name for item in CATALOG]


def select_catalog_item(
    required_development_m: float,
    diameter_mm: int,
    spacing_mm: int,
    required_height_m: float = 0.0,
) -> Optional[CatalogItem]:
    candidates = [
        item for item in CATALOG
        if item.diameter_mm == int(diameter_mm)
        and item.spacing_mm == int(spacing_mm)
        and item.development_m + 1e-9 >= required_development_m
        and item.height_m + 1e-9 >= required_height_m
    ]
    if not candidates:
        return None
    return min(candidates, key=lambda item: item.development_m)
