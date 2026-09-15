# GUNITE — Modern UI

Η νέα έκδοση κρατά την υπάρχουσα Python calculation engine και προσθέτει νέο React/TypeScript frontend με FastAPI.

## 1. Backend

```bash
cd gunite_4p_corrected_v7
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
pip install -r requirements-modern.txt
uvicorn backend.api:app --reload --port 8000
```

## 2. Frontend

```bash
cd frontend
npm install
npm run dev
```

Άνοιξε το URL που εμφανίζει το Vite (συνήθως http://localhost:5173).

## Αρχιτεκτονική

- `gunite_calculator.py`: παραμένει η authoritative calculation engine.
- `catalog.py`: παραμένει η authoritative επιλογή καταλόγου.
- `backend/api.py`: λεπτό API adapter, χωρίς αλλαγή στους τύπους.
- `frontend/`: νέο UI React.

Η παλιά Streamlit εφαρμογή παραμένει διαθέσιμη ως `app.py`.
