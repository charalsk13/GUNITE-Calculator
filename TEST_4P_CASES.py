from gunite_calculator import GuniteInput, calculate

BASE = dict(
    name="K1",
    x1b=45, x2b=45, y1b=35, y2b=35,
    fd_mm=25, corner_fd_mm=25, x_side_fd_mm=16, y_side_fd_mm=16,
    fs_mm=10, spacing_mm=150,
    a1_cm=1.0, a2_cm=0.5, tgun_cm=7.5,
    floor_height_m=3.46, nx=3, ny=3,
)

for option in ("1a", "1b"):
    inp = GuniteInput(**BASE, development_option=option)
    r = calculate(inp)
    print(f"\nΠερίπτωση {option}")
    print(f"Υφιστάμενη: {r.existing_width_m*100:.1f} x {r.existing_height_m*100:.1f} cm")
    print(f"Gunite: {r.gunite_width_m*100:.1f} x {r.gunite_height_m*100:.1f} cm")
    print(f"d: {r.d_cm:.1f} cm")
    print(f"Συνδετήρας: {r.x1s:.1f} x {r.y1s:.1f} cm")
    print(f"Π γεωμετρικό: {r.p_development.geometric_required_m*100:.1f} cm")
    print(f"Π + συγκόλληση: {r.p_development.required_m*100:.1f} cm")
    print(f"Εμπόριο: {r.catalog_name}")
    print(f"Υπόλοιπο ανά άκρο: {r.p_development.surplus_each_end_cm:.1f} cm")
    print(f"Ανάπτυγμα: {r.p_development.final_segments_cm} cm")
