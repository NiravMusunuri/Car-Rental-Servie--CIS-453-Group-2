"""Migrate persistent data before starting the hosted service."""
import os
import subprocess
import sys
from pathlib import Path
Path(os.environ.get("DJANGO_DATA_DIR", ".")).mkdir(parents=True, exist_ok=True)
subprocess.run([sys.executable, "manage.py", "migrate", "--noinput"], check=True)
os.execv(sys.executable, [sys.executable, "serve.py"])
