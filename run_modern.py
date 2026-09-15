from pathlib import Path
import subprocess, sys

ROOT = Path(__file__).resolve().parent
frontend = ROOT / 'frontend'
subprocess.run([sys.executable, '-m', 'uvicorn', 'backend.api:app', '--reload', '--port', '8000'], cwd=ROOT)
