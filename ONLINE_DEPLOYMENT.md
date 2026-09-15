# GUNITE Calculator — Online v8

## Changes in v8
- Project sidebar is organized as a tree: Project → Levels → Elements.
- Each level has global defaults for floor height, tgun, a1 and a2.
- Add level / add element / edit element / remove element controls.
- Element section input is now total X length and total Y width, with 3-decimal entry.
- Φd is a fixed engineering selection: 8, 10, 12, 14, 16, 18, 20, 22, 25, 28, 32 mm.
- dh (Hilti) is visibly disabled for 4-sided jackets and is not used by the 4-sided formulas.
- Longitudinal reinforcement can be differentiated by geometric group: corners, X-side bars, Y-side bars.
- Section drawing reflects the selected diameters by group.
- Beam/obstruction calculation remains ON HOLD and does not execute unsupported rules.
- Excel merged-cell error was fixed.

## Deploy
1. Replace the files in the GitHub repository with this ZIP's contents.
2. Keep `app.py` as the Streamlit main file.
3. Streamlit Community Cloud will redeploy after the commit.
