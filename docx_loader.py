from pathlib import Path
from typing import Dict, List, Optional, Tuple
import re
import unicodedata


def _norm(text: object) -> str:
    text = "" if text is None else str(text)
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if unicodedata.category(ch) != "Mn")
    return " ".join(text.replace("\n", " ").split()).strip().lower()


def _section_from_text(text: object) -> Optional[Tuple[int, int]]:
    m = re.search(r"φ\s*(\d+)\s*/\s*(\d+)", _norm(text), flags=re.IGNORECASE)
    if not m:
        return None
    return int(m.group(1)), int(m.group(2))


def extract_mandyes(docx_path: Path) -> List[Dict[str, object]]:
    """Extract the mandyes catalog from the technical DOCX.

    The DOCX uses section rows such as Φ12/150 followed by product rows.
    Section diameter/spacing is treated as authoritative so a typo such as
    220/10/150 inside the Φ12/150 section cannot silently create a Φ10 item.
    """
    try:
        from docx import Document
    except Exception as exc:
        raise RuntimeError("python-docx is required to parse .docx files") from exc

    doc = Document(str(docx_path))
    results: List[Dict[str, object]] = []

    for table in doc.tables:
        if len(table.rows) < 2:
            continue

        headers = [cell.text.strip() for cell in table.rows[0].cells]
        normalized = [_norm(h) for h in headers]
        if not (any("ονομασ" in h for h in normalized) and any("αναπτυ" in h for h in normalized)):
            continue

        current_group: Optional[Tuple[int, int]] = None

        for row in table.rows[1:]:
            cells = [cell.text.strip() for cell in row.cells]
            row_text = " | ".join(cells)
            group = _section_from_text(row_text)
            if group:
                current_group = group
                # A section header is not a product row.
                if not any(re.search(r"\d+[.,]?\d*\s*[x×/]\s*\d+", c) for c in cells):
                    continue

            row_out: Dict[str, object] = {
                "Ονομασία": None,
                "Αναπτυγμα (m)": None,
                "Ύψος (m)": None,
                "Βαρος (kg)": None,
            }

            for h, c in zip(normalized, cells):
                if "ονομα" in h:
                    row_out["Ονομασία"] = c
                elif "αναπτυ" in h:
                    row_out["Αναπτυγμα (m)"] = c
                elif "υψ" in h:
                    row_out["Ύψος (m)"] = c
                elif "βαρ" in h:
                    row_out["Βαρος (kg)"] = c

            if row_out["Ονομασία"] and row_out["Αναπτυγμα (m)"]:
                # Pass section information to catalog.py without changing the
                # public fields consumed by the rest of the app.
                row_out["_section"] = current_group
                results.append(row_out)

    return results
