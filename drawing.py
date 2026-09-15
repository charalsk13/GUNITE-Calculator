import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle, FancyBboxPatch

__all__ = [
    "draw_section_preview",
    "draw_column_section",
    "draw_jacket_developments",
    "draw_vertical_reinforcement",
    "draw_technical_sheet",
]


def _axis_limits(x1, x2, y1, y2, pad=18):
    xmin = -float(x1) - pad
    xmax = float(x2) + pad
    ymin = -float(y1) - pad
    ymax = float(y2) + pad
    return xmin, xmax, ymin, ymax


def _linspace_positions(start, end, count):
    count = max(int(count), 1)
    if count == 1:
        return [(start + end) / 2.0]
    step = (end - start) / (count - 1)
    return [start + i * step for i in range(count)]


def _unique_points(points, tolerance=1e-6):
    unique = []
    for point in points:
        if not any(abs(point[0] - p[0]) < tolerance and abs(point[1] - p[1]) < tolerance for p in unique):
            unique.append(point)
    return unique


def _rebar_points(res, nx, ny):
    """Return longitudinal bar centers on the actual jacket perimeter."""
    x_left, x_right = -res.x1s, res.x2s
    y_bottom, y_top = -res.y1s, res.y2s
    points = []

    if res.case == "4πλευρος μανδύας":
        # In the DOCX convention x1s/x2s/y1s/y2s are the full side
        # dimensions for the 4Π example, so the physical rectangle is
        # centred at the axes with half-dimensions.
        sx = max(float(res.x1s), float(res.x2s))
        sy = max(float(res.y1s), float(res.y2s))
        x_left, x_right = -sx / 2.0, sx / 2.0
        y_bottom, y_top = -sy / 2.0, sy / 2.0
        xs = _linspace_positions(x_left, x_right, nx)
        ys = _linspace_positions(y_bottom, y_top, ny)
        points += [(x, y_bottom) for x in xs]
        points += [(x, y_top) for x in xs]
        points += [(x_left, y) for y in ys]
        points += [(x_right, y) for y in ys]
    elif "3πλευρος" in res.case:
        xs = _linspace_positions(x_left, x_right, nx)
        ys = _linspace_positions(y_bottom, y_top, ny)
        points += [(x, y_top) for x in xs]
        points += [(x_left, y) for y in ys]
        points += [(x_right, y) for y in ys]
    elif "γωνιακός" in res.case:
        xs = _linspace_positions(x_left, x_right, nx)
        ys = _linspace_positions(y_bottom, y_top, ny)
        points += [(x, y_top) for x in xs]
        points += [(x_right, y) for y in ys]

    return _unique_points(points)


def _group_for_point(point, res):
    x, y = point
    tol = 1e-5
    if res.case == "4πλευρος μανδύας":
        sx = max(float(res.x1s), float(res.x2s))
        sy = max(float(res.y1s), float(res.y2s))
        left, right = -sx / 2.0, sx / 2.0
        bottom, top = -sy / 2.0, sy / 2.0
        if (abs(x-left)<tol or abs(x-right)<tol) and (abs(y-bottom)<tol or abs(y-top)<tol):
            return "Γωνίες"
        if abs(y-bottom)<tol or abs(y-top)<tol:
            return "Πλευρές X"
        return "Πλευρές Y"
    if "3πλευρος" in res.case:
        if abs(y-top)<tol and (abs(x-left)<tol or abs(x-right)<tol):
            return "Γωνίες"
        if abs(y-top)<tol:
            return "Πλευρές X"
        return "Πλευρές Y"
    if "γωνιακός" in res.case:
        if abs(x-right)<tol and abs(y-top)<tol:
            return "Γωνίες"
        if abs(y-top)<tol:
            return "Πλευρές X"
        return "Πλευρές Y"
    return "Πλευρές X"


def _group_diameters(inp):
    return {
        "Γωνίες": float(getattr(inp, "corner_fd_mm", None) or inp.fd_mm),
        "Πλευρές X": float(getattr(inp, "x_side_fd_mm", None) or inp.fd_mm),
        "Πλευρές Y": float(getattr(inp, "y_side_fd_mm", None) or inp.fd_mm),
    }


def _points_on_beam_side(points, res, side):
    tol = 1e-6
    if side == "Αριστερά":
        return sorted([p for p in points if abs(p[0] + res.x1s) < tol], key=lambda p: p[1])
    if side == "Δεξιά":
        return sorted([p for p in points if abs(p[0] - res.x2s) < tol], key=lambda p: p[1])
    if side == "Κάτω":
        return sorted([p for p in points if abs(p[1] + res.y1s) < tol], key=lambda p: p[0])
    if side == "Πάνω":
        return sorted([p for p in points if abs(p[1] - res.y2s) < tol], key=lambda p: p[0])
    return []


def draw_section_preview(x1b, x2b, y1b, y2b, a1_cm, a2_cm, fd_mm, fs_mm, nx, ny, jacket_case="4πλευρος μανδύας"):
    class Result:
        x1s = x1b
        x2s = x2b
        y1s = y1b
        y2s = y2b
        x1g = x1b
        x2g = x2b
        y1g = y1b
        y2g = y2b
        case = jacket_case
        cover_cm = None
        longitudinal_bars_total = 0
        beam_result = None

    res = Result()
    inp = type("Input", (), {"fd_mm": fd_mm, "nx": nx, "ny": ny, "name": "Προεπισκόπηση"})()
    return draw_column_section(inp, res, size="Μεγάλο", show_values=False)


def _dim_h(ax, x0, x1, y, text, ext_y0=None, fontsize=8, color=None):
    """Horizontal dimension with extension lines, in cm coordinates."""
    if ext_y0 is not None:
        ax.plot([x0, x0], [ext_y0, y], linewidth=0.7, color=color)
        ax.plot([x1, x1], [ext_y0, y], linewidth=0.7, color=color)
    ax.annotate("", xy=(x1, y), xytext=(x0, y),
                arrowprops=dict(arrowstyle="<->", linewidth=0.8, color=color))
    ax.text((x0+x1)/2, y + 1.0, text, ha="center", va="bottom", fontsize=fontsize, color=color)


def _dim_v(ax, y0, y1, x, text, ext_x0=None, fontsize=8, color=None):
    """Vertical dimension with extension lines, in cm coordinates."""
    if ext_x0 is not None:
        ax.plot([ext_x0, x], [y0, y0], linewidth=0.7, color=color)
        ax.plot([ext_x0, x], [y1, y1], linewidth=0.7, color=color)
    ax.annotate("", xy=(x, y1), xytext=(x, y0),
                arrowprops=dict(arrowstyle="<->", linewidth=0.8, color=color))
    ax.text(x + 1.0, (y0+y1)/2, text, ha="left", va="center", fontsize=fontsize, rotation=90, color=color)


def _draw_4p_section(ax, inp, res, show_values=True):
    """Faithful 4-sided section drawing following the DOCX example.

    The DOCX convention used by the calculator treats X1b/X2b as the full
    existing side dimensions repeated on the two sides (e.g. 45/45 and
    35/35).  The displayed physical section is therefore 45 x 35 cm, while
    the calculated jacket is 60 x 50 cm for tgun=7.5 cm.
    """
    bx = max(float(inp.x1b), float(inp.x2b))
    by = max(float(inp.y1b), float(inp.y2b))
    gx = max(float(res.x1g), float(res.x2g))
    gy = max(float(res.y1g), float(res.y2g))
    sx = max(float(res.x1s), float(res.x2s))
    sy = max(float(res.y1s), float(res.y2s))

    # Outer Gunite, existing concrete, and stirrup.
    ax.add_patch(Rectangle((-gx/2, -gy/2), gx, gy, fill=False, linewidth=1.8))
    ax.add_patch(Rectangle((-bx/2, -by/2), bx, by, fill=True, alpha=0.14, linewidth=1.2))
    ax.add_patch(Rectangle((-sx/2, -sy/2), sx, sy, fill=False, linewidth=1.2))

    # Axes and labels as in the supplied drawings.
    ax.axhline(0, linestyle="--", linewidth=0.7)
    ax.axvline(0, linestyle="--", linewidth=0.7)
    ax.text(0, gy/2 + 10, "X2", ha="center", va="bottom", fontsize=13)
    ax.text(0, -gy/2 - 10, "X1", ha="center", va="top", fontsize=13)
    ax.text(-gx/2 - 10, 0, "Y1", ha="right", va="center", fontsize=13)
    ax.text(gx/2 + 10, 0, "Y2", ha="left", va="center", fontsize=13)

    # Longitudinal bars: corners Φcorner and intermediate side bars.
    points = _rebar_points(res, int(inp.nx), int(inp.ny))
    diameters = _group_diameters(inp)
    for x, y in points:
        group = _group_for_point((x, y), res)
        radius = max(min(diameters[group] / 14.0, 1.15), 0.65)
        ax.add_patch(Circle((x, y), radius=radius, fill=True, linewidth=0.7))

    if not show_values:
        ax.set_aspect("equal")
        ax.axis("off")
        return

    # Dimension chains closely matching the supplied example.
    _dim_h(ax, -gx/2, gx/2, gy/2 + 5.5, f"{gx:.1f}", ext_y0=gy/2, fontsize=8)
    _dim_h(ax, -gx/2, -bx/2, gy/2 + 2.3, f"{(gx-bx)/2:.1f}", ext_y0=gy/2, fontsize=7)
    _dim_h(ax, -bx/2, bx/2, gy/2 + 2.3, f"{bx:.1f}", ext_y0=gy/2, fontsize=7)
    _dim_h(ax, bx/2, gx/2, gy/2 + 2.3, f"{(gx-bx)/2:.1f}", ext_y0=gy/2, fontsize=7)

    _dim_v(ax, -gy/2, gy/2, -gx/2 - 5.5, f"{gy:.1f}", ext_x0=-gx/2, fontsize=8)
    _dim_v(ax, -by/2, by/2, -gx/2 - 2.3, f"{by:.1f}", ext_x0=-gx/2, fontsize=7)
    _dim_v(ax, -gy/2, -by/2, -gx/2 - 2.3, f"{(gy-by)/2:.1f}", ext_x0=-gx/2, fontsize=7)

    # Stirrup dimensions on the right, matching the source drawing's hierarchy.
    _dim_h(ax, -sx/2, sx/2, -gy/2 - 4.0, f"Συνδετήρας X = {sx:.1f}", fontsize=7)
    _dim_v(ax, -sy/2, sy/2, gx/2 + 4.0, f"{sy:.1f}", fontsize=7)

    # Small construction detail: d = a1 + Φmax/2 + a2 + Φs/2.
    max_fd = max(
        float(getattr(inp, "corner_fd_mm", None) or inp.fd_mm),
        float(getattr(inp, "x_side_fd_mm", None) or inp.fd_mm),
        float(getattr(inp, "y_side_fd_mm", None) or inp.fd_mm),
    )
    max_fd_cm = max_fd / 10.0
    fs_cm = float(inp.fs_mm) / 10.0
    ax.text(-gx/2 + 1.0, -gy/2 - 10.5,
            f"a1={inp.a1_cm:.1f}   maxΦd={max_fd_cm:.1f}   a2={inp.a2_cm:.1f}   Φs={fs_cm:.1f}",
            ha="left", va="top", fontsize=7)
    ax.text(0, -gy/2 - 14.0,
            f"d = {res.d_cm:.1f} cm   |   επικάλυψη c = {res.cover_cm:.1f} cm",
            ha="center", va="top", fontsize=8, fontweight="bold")
    ax.text(0, gy/2 + 9.2,
            f"Gunite {gx:.1f} × {gy:.1f} cm   |   υφιστάμενη {bx:.1f} × {by:.1f} cm",
            ha="center", va="bottom", fontsize=8, fontweight="bold")

    ax.set_aspect("equal")
    pad_x = max(18, 0.35*gx)
    pad_y = max(20, 0.42*gy)
    ax.set_xlim(-gx/2-pad_x, gx/2+pad_x)
    ax.set_ylim(-gy/2-pad_y, gy/2+pad_y)
    ax.axis("off")


def draw_column_section(inp, res, size="Μέτριο", show_values=True):
    """Draw calculated section using the same geometry as the calculator."""
    if isinstance(size, tuple) and len(size) == 2:
        figsize = size
    else:
        figsize = {"Μικρό": (5, 5), "Μέτριο": (7.5, 7.5), "Μεγάλο": (9.5, 8.5)}.get(size, (7.5, 7.5))

    fig, ax = plt.subplots(figsize=figsize)
    is_4p = getattr(res, "case", "") == "4πλευρος μανδύας"
    if is_4p:
        _draw_4p_section(ax, inp, res, show_values=show_values)
    else:
        # Preserve the existing 3Π/2Π drawing until those cases are audited.
        x1b, x2b, y1b, y2b = inp.x1b, inp.x2b, inp.y1b, inp.y2b
        x1g, x2g, y1g, y2g = res.x1g, res.x2g, res.y1g, res.y2g
        bx = x1b + x2b
        by = y1b + y2b
        gx = x1g + x2g
        gy = y1g + y2g
        sx = res.x1s + res.x2s
        sy = res.y1s + res.y2s
        ax.add_patch(Rectangle((-gx/2, -gy/2), gx, gy, fill=False, linewidth=2.2))
        ax.add_patch(Rectangle((-bx/2, -by/2), bx, by, fill=True, alpha=0.18, linewidth=1.3))
        ax.add_patch(Rectangle((-sx/2, -sy/2), sx, sy, fill=False, linewidth=1.5, linestyle="--"))
        points = _rebar_points(res, int(inp.nx), int(inp.ny))
        diameters = _group_diameters(inp)
        for x, y in points:
            group = _group_for_point((x, y), res)
            radius = max(min(diameters[group] / 14.0, 1.15), 0.65)
            ax.add_patch(Circle((x, y), radius=radius, fill=True, linewidth=0.7))
        ax.axhline(0, linestyle="--", linewidth=0.8)
        ax.axvline(0, linestyle="--", linewidth=0.8)
        ax.set_aspect("equal")
        ax.set_xlim(-gx/2-18, gx/2+18)
        ax.set_ylim(-gy/2-18, gy/2+18)
        ax.axis("off")

    ax.set_title(f"{getattr(inp, 'name', 'Στοιχείο')} — {res.case}", fontsize=12, fontweight="bold")
    fig.tight_layout()
    return fig


def draw_jacket_developments(inp, res, size="Μεγάλο"):
    """Draw actual commercial P/Γ developments selected from the catalog."""
    if isinstance(size, tuple) and len(size) == 2:
        figsize = size
    else:
        figsize = {"Μικρό": (8, 3.5), "Μέτριο": (10, 4.5), "Μεγάλο": (12, 5.5)}.get(size, (10, 4.5))

    devs = [res.p_development]
    if res.p_development_bottom is not None:
        devs.append(res.p_development_bottom)

    fig, ax = plt.subplots(figsize=figsize)
    y_positions = list(range(len(devs) - 1, -1, -1))
    max_len = max((d.selected_m or d.required_m) * 100 for d in devs)

    for y, dev in zip(y_positions, devs):
        total = (dev.selected_m or dev.required_m) * 100
        horizontal = dev.adjusted_left_cm + dev.adjusted_right_cm
        leg = dev.adjusted_middle_cm / 2.0
        direction = 1 if y == 0 else -1
        ax.plot([0, horizontal], [y, y], linewidth=3)
        ax.plot([0, 0], [y, y + direction * leg], linewidth=3)
        ax.plot([horizontal, horizontal], [y, y + direction * leg], linewidth=3)
        ax.plot([0, total], [y - 0.32, y - 0.32], linewidth=6, solid_capstyle="butt", alpha=0.25)
        ax.text(total / 2, y + 0.22, f"{dev.label}: απαιτούμενο {dev.required_m:.2f} m", ha="center", va="bottom", fontsize=9)
        selected_text = f"εμπορίου {dev.selected_m:.2f} m" if dev.selected_m else "δεν βρέθηκε προϊόν"
        ax.text(total / 2, y - 0.45, selected_text, ha="center", va="top", fontsize=9)

    ax.set_xlim(-5, max_len + 5)
    ax.set_ylim(-1, len(devs) + 0.4)
    ax.set_yticks([])
    ax.set_xlabel("Ανάπτυγμα (cm)")
    ax.set_title(f"{getattr(inp, 'name', 'Στοιχείο')} — ανάπτυγμα μανδύων", fontweight="bold")
    ax.grid(axis="x", linestyle=":", linewidth=0.7)
    fig.tight_layout()
    return fig


def draw_vertical_reinforcement(inp, res, size="Μεγάλο"):
    """Parametric elevation of the vertical reinforcement.

    When a beam is enabled, its exact lower/top elevations are drawn and the
    selected interrupted bars receive a real graphical gap at that elevation.
    The lower/upper piece lengths remain the user's procurement lengths and are
    shown separately from the geometric beam position.
    """
    figsize = {"Μικρό": (7, 8), "Μέτριο": (8, 9), "Μεγάλο": (9, 10)}.get(size, (9, 10))
    fig, ax = plt.subplots(figsize=figsize)

    H = float(res.main_bar_length_m)
    H_floor = float(inp.floor_height_m)
    wait = float(inp.waiting_m)
    width = 1.0

    # Element/jacket envelope.
    ax.add_patch(Rectangle((-width / 2, 0), width, H_floor, fill=False, linewidth=2.5))
    ax.text(0, H_floor / 2, f"{res.case}\n{res.gunite_width_m*100:.0f}×{res.gunite_height_m*100:.0f} cm",
            ha="center", va="center", fontsize=9)

    n = res.longitudinal_bars_total
    spacing = 0.055
    start = -(max(n - 1, 0) * spacing) / 2

    # Identify which perimeter bars are interrupted at the selected side.
    section_points = _rebar_points(res, int(inp.nx), int(inp.ny))
    interrupted_section = []
    if res.beam_result is not None:
        interrupted_section = _points_on_beam_side(section_points, res, res.beam_result.side)
        interrupted_section = interrupted_section[:res.beam_result.interrupted_bars]

    interrupted_count = len(interrupted_section)
    # In elevation, the exact identity of the selected bars is not spatially
    # resolved left-to-right; draw the first N as interrupted and label this.
    interrupted_indices = set(range(interrupted_count))

    if res.beam_result is None:
        for i in range(n):
            x = start + i * spacing
            ax.plot([x, x], [0, H], linewidth=1.8)
    else:
        b = res.beam_result
        gap_bottom = b.beam_bottom_m
        gap_top = b.beam_top_m
        for i in range(n):
            x = start + i * spacing
            if i in interrupted_indices:
                ax.plot([x, x], [0, gap_bottom], linewidth=1.8)
                ax.plot([x, x], [gap_top, H], linewidth=1.8)
                # Short lap indication on both sides of the interruption.
                lap = min(b.overlap_length_m, max(gap_bottom, 0.0), max(H-gap_top, 0.0))
                if lap > 0:
                    ax.plot([x-0.012, x+0.012], [gap_bottom, gap_bottom], linewidth=1.0)
                    ax.plot([x-0.012, x+0.012], [gap_top, gap_top], linewidth=1.0)
            else:
                ax.plot([x, x], [0, H], linewidth=1.8)

        # Exact beam body crossing the column.
        beam_width = 2.4
        ax.add_patch(Rectangle((-beam_width/2, b.beam_bottom_m), beam_width, b.beam_height_m,
                               fill=True, alpha=0.20, linewidth=1.2))
        ax.text(0, (b.beam_bottom_m + b.beam_top_m)/2,
                f"ΔΟΚΟΣ — {b.side}", ha="center", va="center", fontsize=8, fontweight="bold")
        ax.annotate(f"κάτω στάθμη {b.beam_bottom_m:.2f} m",
                    xy=(beam_width/2, b.beam_bottom_m), xytext=(1.45, b.beam_bottom_m),
                    arrowprops=dict(arrowstyle="->"), va="center", fontsize=8)
        ax.annotate(f"πάνω στάθμη {b.beam_top_m:.2f} m",
                    xy=(beam_width/2, b.beam_top_m), xytext=(1.45, b.beam_top_m),
                    arrowprops=dict(arrowstyle="->"), va="center", fontsize=8)
        ax.text(0, b.beam_top_m + 0.10,
                f"{b.interrupted_bars} διακοπτόμενες / {b.continuous_bars} συνεχείς",
                ha="center", va="bottom", fontsize=8)

    if wait > 0:
        ax.axhline(H_floor, linestyle="--", linewidth=1.0)
        ax.annotate(f"αναμονή {wait:.2f} m", xy=(width / 2 + 0.06, H_floor),
                    xytext=(width / 2 + 0.40, H_floor + wait / 2),
                    arrowprops=dict(arrowstyle="<->"), va="center", fontsize=8)

    ax.annotate(f"μήκος ράβδου = {res.rounded_main_bar_length_m:.2f} m",
                xy=(-0.8, 0), xytext=(-1.6, H / 2),
                arrowprops=dict(arrowstyle="<->"), rotation=90, va="center", ha="center", fontsize=8)

    ax.text(0, H + 0.15, f"{inp.name} — Κατακόρυφη όψη διαμήκων",
            ha="center", va="bottom", fontweight="bold")
    if res.beam_result is not None:
        b = res.beam_result
        status = "OK" if b.lower_piece_ok and b.upper_piece_ok else "ΕΛΕΓΧΟΣ ΜΗΚΩΝ"
        ax.text(0, -0.22,
                f"Μαντάρισμα: κάτω {b.rounded_lower_piece_m:.2f} m · άνω {b.rounded_upper_piece_m:.2f} m · "
                f"υπερκάλυψη {b.overlap_length_m:.2f} m · {status}",
                ha="center", va="top", fontsize=8)
    else:
        ax.text(0, -0.22, "Συνεχείς διαμήκεις ράβδοι", ha="center", va="top", fontsize=8)

    ax.set_xlim(-1.9, 1.9)
    ax.set_ylim(-0.45, H + 0.45)
    ax.axis("off")
    fig.tight_layout()
    return fig

def draw_technical_sheet(inp, res, size="Μεγάλο"):
    """Compact technical sheet: section + longitudinal elevation only.

    The commercial P-development plot is intentionally omitted. Commercial
    jacket selections remain available in the tables and order section.
    """
    fig = plt.figure(figsize=(14, 8))
    grid = fig.add_gridspec(1, 2, width_ratios=[1.15, 0.85])
    ax1 = fig.add_subplot(grid[0, 0])
    ax2 = fig.add_subplot(grid[0, 1])

    x1b, x2b, y1b, y2b = inp.x1b, inp.x2b, inp.y1b, inp.y2b
    bx = max(float(x1b), float(x2b)) if res.case == "4πλευρος μανδύας" else float(x1b + x2b)
    by = max(float(y1b), float(y2b)) if res.case == "4πλευρος μανδύας" else float(y1b + y2b)
    gx = max(float(res.x1g), float(res.x2g)) if res.case == "4πλευρος μανδύας" else float(res.x1g + res.x2g)
    gy = max(float(res.y1g), float(res.y2g)) if res.case == "4πλευρος μανδύας" else float(res.y1g + res.y2g)

    # Section
    ax1.add_patch(Rectangle((-gx/2, -gy/2), gx, gy, fill=False, linewidth=2.5))
    ax1.add_patch(Rectangle((-bx/2, -by/2), bx, by, fill=True, alpha=0.18, linewidth=1.2))
    if res.case == "4πλευρος μανδύας":
        sx = max(float(res.x1s), float(res.x2s)) / 2.0
        sy = max(float(res.y1s), float(res.y2s)) / 2.0
        ax1.add_patch(Rectangle((-sx, -sy), 2*sx, 2*sy, fill=False, linewidth=1.5, linestyle="--"))
    else:
        ax1.add_patch(Rectangle((-res.x1s, -res.y1s), res.x1s + res.x2s, res.y1s + res.y2s, fill=False, linewidth=1.5, linestyle="--"))

    diameters = {
        "Γωνίες": float(getattr(inp, "corner_fd_mm", None) or inp.fd_mm),
        "Πλευρές X": float(getattr(inp, "x_side_fd_mm", None) or inp.fd_mm),
        "Πλευρές Y": float(getattr(inp, "y_side_fd_mm", None) or inp.fd_mm),
    }
    for x, y in _rebar_points(res, inp.nx, inp.ny):
        group = _group_for_point((x, y), res)
        radius = max(min(diameters[group] / 6.0, 2.8), 1.4)
        ax1.add_patch(Circle((x, y), radius=radius, fill=True, alpha=0.95))

    ax1.axhline(0, linestyle=":", linewidth=0.8)
    ax1.axvline(0, linestyle=":", linewidth=0.8)
    ax1.set_aspect("equal")
    lims = _axis_limits(res.x1g, res.x2g, res.y1g, res.y2g, 18)
    ax1.set_xlim(lims[0], lims[1]); ax1.set_ylim(lims[2], lims[3]); ax1.axis("off")
    ax1.set_title(
        f"Διατομή — {inp.name}\n"
        f"Υφιστάμενη {bx:.1f}×{by:.1f} cm · Gunite {gx:.1f}×{gy:.1f} cm\n"
        f"Συνδετήρας {max(float(res.x1s), float(res.x2s)) if res.case == '4πλευρος μανδύας' else res.x1s+res.x2s:.1f}×{max(float(res.y1s), float(res.y2s)) if res.case == '4πλευρος μανδύας' else res.y1s+res.y2s:.1f} cm",
        fontweight="bold", fontsize=11)

    # Elevation
    H = float(res.main_bar_length_m)
    ax2.add_patch(Rectangle((-0.5, 0), 1.0, inp.floor_height_m, fill=False, linewidth=2.0))
    for i in range(res.longitudinal_bars_total):
        x = (i - (res.longitudinal_bars_total - 1) / 2) * 0.05
        ax2.plot([x, x], [0, H], linewidth=1.5)
    ax2.axhline(inp.floor_height_m, linestyle="--", linewidth=0.8)
    ax2.set_xlim(-1.6, 1.6); ax2.set_ylim(-0.2, H + 0.2); ax2.axis("off")
    ax2.set_title(f"Κατακόρυφη όψη — ύψος ορόφου {inp.floor_height_m:.2f} m", fontweight="bold")

    fig.suptitle(
        f"GUNITE — ΤΕΧΝΙΚΟ ΦΥΛΛΟ {inp.name}\n"
        f"{res.case} · {res.longitudinal_bars_total} διαμήκεις · Gunite {res.gunite_volume_m3:.3f} m³",
        fontsize=14, fontweight="bold")
    fig.tight_layout(rect=[0, 0, 1, 0.90])
    return fig

