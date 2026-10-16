"""Isolated subprocess boundary avoids collisions with rubrics' standalone modules."""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def context(task):
    result = subprocess.run([sys.executable, '-B', str(ROOT / 'rubrics/src/bridge.py')],
                            input=json.dumps({'project': 'research', 'task': task}, ensure_ascii=False),
                            capture_output=True, text=True, timeout=30, check=True)
    return result.stdout.strip()


def refresh_attention():
    subprocess.run([sys.executable, '-B', str(ROOT / 'rubrics/src/activity.py')],
                   check=True, timeout=60)
