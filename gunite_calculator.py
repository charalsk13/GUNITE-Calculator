from dataclasses import dataclass
from math import ceil, pi
from typing import Dict, List, Optional

from catalog import CatalogItem, select_catalog_item

EPS = 1e-6


@dataclass
class BeamObstruction:
    enabled: bool = False
    side: str = "Καμία"
    interrupted_bars: int = 0
    # Exact vertical position of the beam in the floor/element elevation.
    # beam_bottom_m is measured from the bottom of the modeled floor height.
    beam_bottom_m: float = 1.20
    beam_height_m: float = 0.50
    lower_piece_m: float = 3.00
    upper_piece_m: float = 2.00


@dataclass
class GuniteInput:
    name: str
    # X1/X2/Y1/Y2 are distances from the column axes to the existing faces.
    x1b: float
    x2b: float
    y1b: float
    y2b: float
    fd_mm: float = 25.0
    corner_fd_mm: Optional[float] = None
    x_side_fd_mm: Optional[float] = None
    y_side_fd_mm: Optional[float] = None
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
    beam: Optional[BeamObstruction] = None
    # For 4Π only: source drawing offers two P-development arrangements.
    development_option: str = "1a"


@dataclass
class PJacketingDevelopment:
    required_m: float
    geometric_required_m: float
    selected_m: Optional[float]
    left_cm: float
    middle_cm: float
    right_cm: float
    adjusted_left_cm: float
    adjusted_middle_cm: float
    adjusted_right_cm: float
    welding_half_cm: float = 0.0
    surplus_each_end_cm: float = 0.0
    final_segments_cm: str = ""
    label: str = "Π"


@dataclass
class BeamResult:
    enabled: bool
    side: str
    interrupted_bars: int
    continuous_bars: int
    beam_bottom_m: float
    beam_top_m: float
    beam_height_m: float
    lower_piece_m: float
    rounded_lower_piece_m: float
    upper_piece_m: float
    rounded_upper_piece_m: float
    overlap_length_m: float
    lower_required_m: float
    upper_required_m: float
    lower_piece_ok: bool
    upper_piece_ok: bool


@dataclass
class GuniteResult:
    case: str
    d_cm: float

    # Distances from axes to faces, exactly as defined in the theory document.
    x1g: float
    x2g: float
    y1g: float
    y2g: float
    x1s: float
    x2s: float
    y1s: float
    y2s: float

    cover_cm: Optional[float]

    # For 4-sided jackets these are the top and bottom P pieces separately.
    p_development: PJacketingDevelopment
    p_development_bottom: Optional[PJacketingDevelopment]
    catalog_name: Optional[str]
    catalog_weight_kg: Optional[float]
    catalog_height_m: Optional[float]
    catalog_name_bottom: Optional[str]
    catalog_weight_kg_bottom: Optional[float]
    catalog_height_m_bottom: Optional[float]

    # Kept for simple UI/project summaries: top/primary jacket values.
    theoretical_development_m: float
    selected_development_m: Optional[float]

    longitudinal_bars_total: int
    main_bar_length_m: float
    rounded_main_bar_length_m: float
    overlap_length_m: float

    beam_result: Optional[BeamResult]

    existing_width_m: float
    existing_height_m: float
    gunite_width_m: float
    gunite_height_m: float
    gunite_perimeter_m: float
    existing_perimeter_m: float
    gunite_surface_m2: float
    existing_surface_m2: float
    gunite_volume_m3: float
    jacket_total_weight_kg: Optional[float]
    longitudinal_groups: Dict[str, Dict[str, float]]


def is_zero(value: float) -> bool:
    return abs(value) < EPS


def round_up_to_step(value: float, step: float = 0.05) -> float:
    if value <= EPS:
        return 0.0
    return ceil(value / step - EPS) * step


def select_development(required_m: float, diameter_mm: int, spacing_mm: int, required_height_cm: float = 0.0) -> Optional[CatalogItem]:
    """Return an actual catalog item, never a synthetic/hard-coded development."""
    return select_catalog_item(required_m, diameter_mm, spacing_mm, required_height_m=required_height_cm / 100.0)


def _make_p_development(label: str, left_cm: float, middle_cm: float, right_cm: float,
                        welding_half_cm: float = 0.0) -> PJacketingDevelopment:
    # The three geometric parts are the two half-legs and the middle side.
    # For the 4Π source examples, the welding/overlap allowance is added at
    # both ends before the commercial length is selected.
    geometric_m = (left_cm + middle_cm + right_cm) / 100.0
    required_m = geometric_m + (2.0 * welding_half_cm) / 100.0
    return PJacketingDevelopment(
        required_m=round(required_m, 3),
        geometric_required_m=round(geometric_m, 3),
        selected_m=None,
        left_cm=round(left_cm, 3),
        middle_cm=round(middle_cm, 3),
        right_cm=round(right_cm, 3),
        adjusted_left_cm=round(left_cm + welding_half_cm, 3),
        adjusted_middle_cm=round(middle_cm, 3),
        adjusted_right_cm=round(right_cm + welding_half_cm, 3),
        welding_half_cm=round(welding_half_cm, 3),
        surplus_each_end_cm=0.0,
        final_segments_cm="",
        label=label,
    )


def _apply_catalog_to_development(dev: PJacketingDevelopment, item: Optional[CatalogItem]) -> PJacketingDevelopment:
    if item is None:
        return dev

    selected_cm = item.development_m * 100.0
    surplus_cm = max(selected_cm - dev.required_m * 100.0, 0.0)
    surplus_each = surplus_cm / 2.0
    # The source drawing distributes commercial surplus equally to the two
    # free ends. Keep the geometric middle/legs intact and expose the final
    # seven-part chain explicitly for the UI: surplus/2 + weld/2 + leg +
    # middle + leg + weld/2 + surplus/2.
    final_segments = (
        f"{surplus_each:.1f} + {dev.welding_half_cm:.1f} + "
        f"{dev.left_cm:.1f} + {dev.middle_cm:.1f} + {dev.right_cm:.1f} + "
        f"{dev.welding_half_cm:.1f} + {surplus_each:.1f}"
    )
    return PJacketingDevelopment(
        required_m=dev.required_m,
        geometric_required_m=dev.geometric_required_m,
        selected_m=round(item.development_m, 3),
        left_cm=dev.left_cm,
        middle_cm=dev.middle_cm,
        right_cm=dev.right_cm,
        adjusted_left_cm=round(dev.left_cm + dev.welding_half_cm + surplus_each, 3),
        adjusted_middle_cm=dev.middle_cm,
        adjusted_right_cm=round(dev.right_cm + dev.welding_half_cm + surplus_each, 3),
        welding_half_cm=dev.welding_half_cm,
        surplus_each_end_cm=round(surplus_each, 3),
        final_segments_cm=final_segments,
        label=dev.label,
    )


def detect_case(inp: GuniteInput) -> str:
    if inp.x1b > EPS and inp.x2b > EPS and inp.y1b > EPS and inp.y2b > EPS:
        return "4πλευρος μανδύας"

    if is_zero(inp.y1b) and inp.x1b > EPS and inp.x2b > EPS and inp.y2b > EPS:
        return "3πλευρος μανδύας - ελεύθερη κάτω πλευρά"

    if is_zero(inp.x1b) and is_zero(inp.y1b) and inp.x2b > EPS and inp.y2b > EPS:
        return "γωνιακός μανδύας"

    return "μη τυπική περίπτωση"


def calculate_beam_result(inp: GuniteInput, total_bars: int, overlap_len: float) -> Optional[BeamResult]:
    if inp.beam is None or not inp.beam.enabled:
        return None

    interrupted = max(0, min(inp.beam.interrupted_bars, total_bars))
    continuous = max(total_bars - interrupted, 0)
    bottom = float(inp.beam.beam_bottom_m)
    height = float(inp.beam.beam_height_m)
    top = bottom + height
    if bottom < 0 or height <= 0 or top > inp.floor_height_m + EPS:
        raise ValueError(
            f"Η θέση δοκού δεν είναι έγκυρη: κάτω στάθμη={bottom:.2f} m, "
            f"ύψος={height:.2f} m, ύψος ορόφου={inp.floor_height_m:.2f} m."
        )

    # Minimum geometric lengths from the floor base/top. The requested
    # lower/upper piece lengths remain user-controlled, but are checked
    # against the geometry plus one lap length.
    lower_required = bottom + overlap_len
    upper_required = max(inp.floor_height_m - top, 0.0) + overlap_len + inp.waiting_m

    return BeamResult(
        enabled=True,
        side=inp.beam.side,
        interrupted_bars=interrupted,
        continuous_bars=continuous,
        beam_bottom_m=round(bottom, 3),
        beam_top_m=round(top, 3),
        beam_height_m=round(height, 3),
        lower_piece_m=round(inp.beam.lower_piece_m, 3),
        rounded_lower_piece_m=round(round_up_to_step(inp.beam.lower_piece_m, 0.05), 3),
        upper_piece_m=round(inp.beam.upper_piece_m, 3),
        rounded_upper_piece_m=round(round_up_to_step(inp.beam.upper_piece_m, 0.05), 3),
        overlap_length_m=round(overlap_len, 3),
        lower_required_m=round(lower_required, 3),
        upper_required_m=round(upper_required, 3),
        lower_piece_ok=inp.beam.lower_piece_m + EPS >= lower_required,
        upper_piece_ok=inp.beam.upper_piece_m + EPS >= upper_required,
    )


def calculate_d(inp: GuniteInput, max_fd_mm: Optional[float] = None) -> float:
    # d = a1 + max(Φd)/10 + a2 + Φs/10, all in cm.
    # For 4Π the source example explicitly uses maxΦd when different
    # longitudinal diameters exist (e.g. 4Φ25 + 4Φ16 -> maxΦd = 25 mm).
    fd_for_d = float(max_fd_mm if max_fd_mm is not None else inp.fd_mm)
    return inp.a1_cm + fd_for_d / 10.0 + inp.a2_cm + inp.fs_mm / 10.0


def calculate_4_sided_dimensions(inp: GuniteInput, d: float):
    # For 4Π the DOCX uses the full existing side dimensions on each axis
    # (e.g. X1b=X2b=45 cm, Y1b=Y2b=35 cm). The jacket grows by 2*tgun
    # overall, and the stirrup dimension grows by 2*d overall.
    x1g = inp.x1b + 2 * inp.tgun_cm
    x2g = inp.x2b + 2 * inp.tgun_cm
    y1g = inp.y1b + 2 * inp.tgun_cm
    y2g = inp.y2b + 2 * inp.tgun_cm

    x1s = inp.x1b + 2 * d
    x2s = inp.x2b + 2 * d
    y1s = inp.y1b + 2 * d
    y2s = inp.y2b + 2 * d

    # Cover between the outer Gunite face and the outside of the stirrup.
    cover = (x1g - x1s) / 2.0
    return x1g, x2g, y1g, y2g, x1s, x2s, y1s, y2s, cover


def calculate_3_sided_dimensions(inp: GuniteInput, d: float):
    # Theory: Y1b=0 is the free lower side. Gunite grows by tgun on the two
    # side faces and 2*tgun on the closed upper face.
    x1g = inp.x1b + inp.tgun_cm
    x2g = inp.x2b + inp.tgun_cm
    y1g = 0.0
    y2g = inp.y2b + 2 * inp.tgun_cm

    x1s = (inp.x1b + d) - inp.dh_cm
    x2s = (inp.x2b + d) - inp.dh_cm
    y1s = 0.0
    y2s = inp.y2b + 2 * d

    return x1g, x2g, y1g, y2g, x1s, x2s, y1s, y2s, None


def calculate_corner_dimensions(inp: GuniteInput, d: float):
    x1g = 0.0
    x2g = inp.x2b + inp.tgun_cm
    y1g = 0.0
    y2g = inp.y2b + inp.tgun_cm

    x1s = 0.0
    x2s = (inp.x2b + d) - inp.dh_cm
    y1s = 0.0
    y2s = (inp.y2b + d) - inp.dh_cm

    return x1g, x2g, y1g, y2g, x1s, x2s, y1s, y2s, None


def calculate_longitudinal_bars(case: str, nx: int, ny: int) -> int:
    """Count unique perimeter longitudinal bars according to the available sides."""
    nx = max(int(nx), 0)
    ny = max(int(ny), 0)

    if case == "4πλευρος μανδύας":
        # Top + bottom rows and left + right rows, with four corner duplicates removed.
        return max((2 * nx) + (2 * ny) - 4, 0)

    if "3πλευρος" in case:
        # Top row + two vertical rows. The two top corners are common points.
        return max(nx + (2 * ny) - 2, 0)

    if "γωνιακός" in case:
        # Only the top and right rows remain; their common corner is counted once.
        return max(nx + ny - 1, 0)

    return 0


def longitudinal_group_counts(case: str, nx: int, ny: int) -> Dict[str, int]:
    """Unique longitudinal bars by geometric group (corners / X sides / Y sides)."""
    nx, ny = max(int(nx), 1), max(int(ny), 1)
    if case == "4πλευρος μανδύας":
        return {"Γωνίες": 4, "Πλευρές X": 2 * max(nx - 2, 0), "Πλευρές Y": 2 * max(ny - 2, 0)}
    if "3πλευρος" in case:
        return {"Γωνίες": 2, "Πλευρές X": max(nx - 2, 0), "Πλευρές Y": 2 * max(ny - 1, 0)}
    if "γωνιακός" in case:
        return {"Γωνίες": 1, "Πλευρές X": max(nx - 1, 0), "Πλευρές Y": max(ny - 1, 0)}
    return {"Γωνίες": 0, "Πλευρές X": 0, "Πλευρές Y": 0}


def longitudinal_group_diameters(inp: GuniteInput) -> Dict[str, float]:
    return {
        "Γωνίες": float(inp.corner_fd_mm or inp.fd_mm),
        "Πλευρές X": float(inp.x_side_fd_mm or inp.fd_mm),
        "Πλευρές Y": float(inp.y_side_fd_mm or inp.fd_mm),
    }


def calculate_premetrisi(inp: GuniteInput, res_case: str, x1g: float, x2g: float, y1g: float, y2g: float) -> Dict[str, float]:
    # 4Π follows the DOCX convention: X1/X2 and Y1/Y2 repeat the full
    # side dimensions (e.g. 45/45 and 35/35), not two half-dimensions.
    # Therefore the physical section dimension is represented by one of the
    # equal paired values (max is also safe for the symmetric 4Π case).
    if res_case == "4πλευρος μανδύας":
        existing_width_m = max(inp.x1b, inp.x2b) / 100.0
        existing_height_m = max(inp.y1b, inp.y2b) / 100.0
        gunite_width_m = max(x1g, x2g) / 100.0
        gunite_height_m = max(y1g, y2g) / 100.0
    else:
        existing_width_m = (inp.x1b + inp.x2b) / 100.0
        existing_height_m = (inp.y1b + inp.y2b) / 100.0
        gunite_width_m = (x1g + x2g) / 100.0
        gunite_height_m = (y1g + y2g) / 100.0

    if res_case == "4πλευρος μανδύας":
        existing_perimeter_m = 2 * (existing_width_m + existing_height_m)
        gunite_perimeter_m = 2 * (gunite_width_m + gunite_height_m)
    elif "3πλευρος" in res_case:
        existing_perimeter_m = existing_width_m + 2 * existing_height_m
        gunite_perimeter_m = gunite_width_m + 2 * gunite_height_m
    elif "γωνιακός" in res_case:
        existing_perimeter_m = existing_width_m + existing_height_m
        gunite_perimeter_m = gunite_width_m + gunite_height_m
    else:
        raise ValueError("Μη τυπική περίπτωση: δεν μπορεί να υπολογιστεί περίμετρος.")

    existing_surface_m2 = existing_perimeter_m * inp.floor_height_m
    gunite_surface_m2 = gunite_perimeter_m * inp.floor_height_m

    existing_area_m2 = existing_width_m * existing_height_m
    gunite_area_m2 = gunite_width_m * gunite_height_m
    gunite_volume_m3 = max(gunite_area_m2 - existing_area_m2, 0.0) * inp.floor_height_m

    return {
        "existing_width_m": round(existing_width_m, 3),
        "existing_height_m": round(existing_height_m, 3),
        "gunite_width_m": round(gunite_width_m, 3),
        "gunite_height_m": round(gunite_height_m, 3),
        "existing_perimeter_m": round(existing_perimeter_m, 3),
        "gunite_perimeter_m": round(gunite_perimeter_m, 3),
        "existing_surface_m2": round(existing_surface_m2, 3),
        "gunite_surface_m2": round(gunite_surface_m2, 3),
        "gunite_volume_m3": round(gunite_volume_m3, 3),
    }


def calculate(inp: GuniteInput) -> GuniteResult:
    if min(inp.x1b, inp.x2b, inp.y1b, inp.y2b, inp.tgun_cm, inp.fd_mm, inp.fs_mm) < -EPS:
        raise ValueError("Οι διαστάσεις δεν μπορούν να είναι αρνητικές.")
    if inp.floor_height_m <= 0:
        raise ValueError("Το ύψος ορόφου πρέπει να είναι θετικό.")
    if inp.nx < 1 or inp.ny < 1:
        raise ValueError("Οι αριθμοί nx και ny πρέπει να είναι τουλάχιστον 1.")

    case = detect_case(inp)
    if case == "4πλευρος μανδύας":
        max_fd_mm = max(
            float(inp.fd_mm),
            float(inp.corner_fd_mm or inp.fd_mm),
            float(inp.x_side_fd_mm or inp.fd_mm),
            float(inp.y_side_fd_mm or inp.fd_mm),
        )
        d = calculate_d(inp, max_fd_mm=max_fd_mm)
    else:
        d = calculate_d(inp)
    if case == "μη τυπική περίπτωση":
        raise ValueError("Η γεωμετρία δεν αντιστοιχεί σε 4πλευρο, 3πλευρο ή γωνιακό μανδύα.")

    if case == "4πλευρος μανδύας":
        x1g, x2g, y1g, y2g, x1s, x2s, y1s, y2s, cover = calculate_4_sided_dimensions(inp, d)
        # Two P-shaped jackets. The supplied reference distinguishes two
        # arrangements for the same 4Π section:
        # 1a: middle side = Xs, half-legs = Ys/2
        # 1b: middle side = Ys, half-legs = Xs/2
        # Both include the welding half-length at each end before commercial
        # selection. For Φ10 the source example gives 6 cm per end, so the
        # 100 cm geometric P becomes 112 cm and selects the 120 cm item.
        weld_half_cm = 2.0 + 0.4 * float(inp.fs_mm)
        option = str(getattr(inp, "development_option", "1a") or "1a").lower()
        if option not in {"1a", "1b"}:
            option = "1a"
        if option == "1a":
            left_leg = y1s / 2.0
            middle = max(x1s, x2s)
            right_leg = y2s / 2.0
        else:
            left_leg = x1s / 2.0
            middle = max(y1s, y2s)
            right_leg = x2s / 2.0
        top_dev_raw = _make_p_development("Πάνω Π", left_leg, middle, right_leg, weld_half_cm)
        bottom_dev_raw = _make_p_development("Κάτω Π", left_leg, middle, right_leg, weld_half_cm)
        top_item = select_development(top_dev_raw.required_m, int(inp.fs_mm), int(inp.spacing_mm), required_height_cm=min(y1s, y2s))
        bottom_item = select_development(bottom_dev_raw.required_m, int(inp.fs_mm), int(inp.spacing_mm), required_height_cm=min(y1s, y2s))
        p_dev = _apply_catalog_to_development(top_dev_raw, top_item)
        p_dev_bottom = _apply_catalog_to_development(bottom_dev_raw, bottom_item)
    elif "3πλευρος" in case:
        x1g, x2g, y1g, y2g, x1s, x2s, y1s, y2s, cover = calculate_3_sided_dimensions(inp, d)
        # U/P-shaped piece: top horizontal segment + two vertical legs.
        p_raw = _make_p_development("Πάνω Π", x1s, 2 * y2s, x2s)
        item = select_development(p_raw.required_m, int(inp.fs_mm), int(inp.spacing_mm), required_height_cm=y2s)
        p_dev = _apply_catalog_to_development(p_raw, item)
        p_dev_bottom = None
        top_item, bottom_item = item, None
    else:
        x1g, x2g, y1g, y2g, x1s, x2s, y1s, y2s, cover = calculate_corner_dimensions(inp, d)
        p_raw = _make_p_development("Γωνιακό Π", x2s, y2s, 0.0)
        item = select_development(p_raw.required_m, int(inp.fs_mm), int(inp.spacing_mm), required_height_cm=y2s)
        p_dev = _apply_catalog_to_development(p_raw, item)
        p_dev_bottom = None
        top_item, bottom_item = item, None

    group_counts = longitudinal_group_counts(case, inp.nx, inp.ny)
    total_bars = sum(group_counts.values())
    main_len = inp.floor_height_m + inp.waiting_m
    rounded_main_len = round_up_to_step(main_len, 0.05)
    overlap_len = inp.overlap_factor * inp.fd_mm / 1000.0
    # Beam/obstruction rules remain on hold until a complete source rule is supplied.
    beam_result = None
    prem = calculate_premetrisi(inp, case, x1g, x2g, y1g, y2g)

    group_diams = longitudinal_group_diameters(inp)
    longitudinal_groups = {}
    for group, count in group_counts.items():
        diameter = group_diams[group]
        longitudinal_groups[group] = {
            "count": float(count),
            "diameter_mm": float(diameter),
            "overlap_m": round(inp.overlap_factor * diameter / 1000.0, 3),
            "length_m": round(rounded_main_len, 3),
        }

    weights = [item.weight_kg for item in (top_item, bottom_item) if item is not None]
    jacket_total_weight = round(sum(weights), 3) if weights else None

    return GuniteResult(
        case=case,
        d_cm=round(d, 3),
        x1g=round(x1g, 3), x2g=round(x2g, 3), y1g=round(y1g, 3), y2g=round(y2g, 3),
        x1s=round(x1s, 3), x2s=round(x2s, 3), y1s=round(y1s, 3), y2s=round(y2s, 3),
        cover_cm=None if cover is None else round(cover, 3),
        p_development=p_dev,
        p_development_bottom=p_dev_bottom,
        catalog_name=None if top_item is None else top_item.name,
        catalog_weight_kg=None if top_item is None else top_item.weight_kg,
        catalog_height_m=None if top_item is None else top_item.height_m,
        catalog_name_bottom=None if bottom_item is None else bottom_item.name,
        catalog_weight_kg_bottom=None if bottom_item is None else bottom_item.weight_kg,
        catalog_height_m_bottom=None if bottom_item is None else bottom_item.height_m,
        theoretical_development_m=p_dev.required_m,
        selected_development_m=None if top_item is None else top_item.development_m,
        longitudinal_bars_total=total_bars,
        main_bar_length_m=round(main_len, 3),
        rounded_main_bar_length_m=round(rounded_main_len, 3),
        overlap_length_m=round(overlap_len, 3),
        beam_result=beam_result,
        existing_width_m=prem["existing_width_m"],
        existing_height_m=prem["existing_height_m"],
        gunite_width_m=prem["gunite_width_m"],
        gunite_height_m=prem["gunite_height_m"],
        gunite_perimeter_m=prem["gunite_perimeter_m"],
        existing_perimeter_m=prem["existing_perimeter_m"],
        gunite_surface_m2=prem["gunite_surface_m2"],
        existing_surface_m2=prem["existing_surface_m2"],
        gunite_volume_m3=prem["gunite_volume_m3"],
        jacket_total_weight_kg=jacket_total_weight,
        longitudinal_groups=longitudinal_groups,
    )


def result_table(inp: GuniteInput, res: GuniteResult) -> List[Dict[str, str]]:
    p = res.p_development
    rows = [
        {"Κατηγορία": "Στοιχείο", "Τιμή": inp.name},
        {"Κατηγορία": "Περίπτωση", "Τιμή": res.case},
        {"Κατηγορία": "d", "Τιμή": f"{res.d_cm:.2f} cm"},
        {"Κατηγορία": "Υφιστάμενη συνολική διατομή", "Τιμή": f"{res.existing_width_m*100:.1f} × {res.existing_height_m*100:.1f} cm"},
        {"Κατηγορία": "Τελική συνολική διατομή gunite", "Τιμή": f"{res.gunite_width_m*100:.1f} × {res.gunite_height_m*100:.1f} cm"},
        {"Κατηγορία": "Αποστάσεις gunite από άξονες", "Τιμή": f"X1g={res.x1g} | X2g={res.x2g} | Y1g={res.y1g} | Y2g={res.y2g} cm"},
        {"Κατηγορία": "Διαστάσεις συνδετήρα", "Τιμή": f"X1s={res.x1s} | X2s={res.x2s} | Y1s={res.y1s} | Y2s={res.y2s} cm"},
        {"Κατηγορία": "Τρόπος ανάπτυξης 4Π", "Τιμή": getattr(inp, "development_option", "1a")},
        {"Κατηγορία": f"{p.label} - γεωμετρικό", "Τιμή": f"{p.left_cm:.1f} + {p.middle_cm:.1f} + {p.right_cm:.1f} cm = {p.geometric_required_m*100:.1f} cm"},
        {"Κατηγορία": f"{p.label} - + συγκόλληση", "Τιμή": f"{p.geometric_required_m*100:.1f} + 2×{p.welding_half_cm:.1f} = {p.required_m*100:.1f} cm"},
        {"Κατηγορία": f"{p.label} - εμπορίου", "Τιμή": f"{res.catalog_name} | {res.selected_development_m:.2f} m | υπόλοιπο {p.surplus_each_end_cm:.1f} cm/άκρο" if res.catalog_name else "Δεν βρέθηκε πραγματικό προϊόν"},
    ]

    if res.p_development_bottom is not None:
        pb = res.p_development_bottom
        rows.extend([
            {"Κατηγορία": f"{pb.label} - γεωμετρικό", "Τιμή": f"{pb.left_cm:.1f} + {pb.middle_cm:.1f} + {pb.right_cm:.1f} cm = {pb.geometric_required_m*100:.1f} cm"},
            {"Κατηγορία": f"{pb.label} - + συγκόλληση", "Τιμή": f"{pb.geometric_required_m*100:.1f} + 2×{pb.welding_half_cm:.1f} = {pb.required_m*100:.1f} cm"},
            {"Κατηγορία": f"{pb.label} - εμπορίου", "Τιμή": f"{res.catalog_name_bottom} | {pb.selected_m:.2f} m | υπόλοιπο {pb.surplus_each_end_cm:.1f} cm/άκρο" if res.catalog_name_bottom else "Δεν βρέθηκε πραγματικό προϊόν"},
        ])

    rows.extend([
        {"Κατηγορία": "Βάρος μανδυών στοιχείου", "Τιμή": f"{res.jacket_total_weight_kg:.2f} kg" if res.jacket_total_weight_kg is not None else "-"},
        {"Κατηγορία": "Περίμετρος gunite", "Τιμή": f"{res.gunite_perimeter_m:.2f} m"},
        {"Κατηγορία": "Επιφάνεια gunite", "Τιμή": f"{res.gunite_surface_m2:.2f} m²"},
        {"Κατηγορία": "Όγκος gunite", "Τιμή": f"{res.gunite_volume_m3:.3f} m³"},
        {"Κατηγορία": "Προσαρμοσμένος Π-μανδύας", "Τιμή": f"{p.adjusted_left_cm:.1f} + {p.adjusted_middle_cm:.1f} + {p.adjusted_right_cm:.1f} cm"},
        {"Κατηγορία": "Διαμήκεις ράβδοι", "Τιμή": f"{res.longitudinal_bars_total} τεμ. Φ{inp.fd_mm:.0f}"},
        {"Κατηγορία": "Μήκος διαμήκους", "Τιμή": f"{res.main_bar_length_m:.2f} m → {res.rounded_main_bar_length_m:.2f} m"},
        {"Κατηγορία": "Μήκος υπερκάλυψης", "Τιμή": f"{res.overlap_length_m:.2f} m"},
    ])

    if res.beam_result is not None:
        b = res.beam_result
        rows.extend([
            {"Κατηγορία": "Δοκός / εμπόδιο", "Τιμή": f"Ναι - {b.side}"},
            {"Κατηγορία": "Ράβδοι που διακόπτονται", "Τιμή": f"{b.interrupted_bars} τεμ."},
            {"Κατηγορία": "Συνεχείς ράβδοι", "Τιμή": f"{b.continuous_bars} τεμ."},
        ])
    return rows


def _steel_mass_per_m(fd_mm: float) -> float:
    steel_density = 7850.0
    d_m = fd_mm / 1000.0
    return (pi * (d_m ** 2) / 4.0) * steel_density


def order_rows(inp: GuniteInput, res: GuniteResult) -> List[Dict[str, object]]:
    rows: List[Dict[str, object]] = []

    jacket_specs = [(res.p_development, res.catalog_name, res.catalog_weight_kg)]
    if res.p_development_bottom is not None:
        jacket_specs.append((res.p_development_bottom, res.catalog_name_bottom, res.catalog_weight_kg_bottom))

    for dev, name, weight in jacket_specs:
        rows.append({
            "Στοιχείο": inp.name,
            "Θέση": dev.label,
            "Τύπος": "Μανδύας εμπορίου",
            "Περιγραφή": name if name is not None else f"Απαιτούμενο {dev.required_m:.2f} m (δεν βρέθηκε προϊόν)",
            "Τεμάχια": 1,
            "Μήκος (m)": dev.selected_m,
            "Βάρος/τεμ (kg)": weight,
            "Σύνολο kg": weight,
        })

    for group, info in res.longitudinal_groups.items():
        count = int(info["count"])
        if count <= 0:
            continue
        diameter = float(info["diameter_mm"])
        length = float(info["length_m"])
        mass_per_m = _steel_mass_per_m(diameter)
        weight_per_piece = round(mass_per_m * length, 3)
        rows.append({
            "Στοιχείο": inp.name,
            "Θέση": group,
            "Τύπος": "Διαμήκης οπλισμός",
            "Περιγραφή": f"Φ{diameter:.0f} συνεχής",
            "Τεμάχια": count,
            "Μήκος (m)": length,
            "Βάρος/τεμ (kg)": weight_per_piece,
            "Σύνολο kg": round(weight_per_piece * count, 3),
        })

    return rows
