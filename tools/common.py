"""Shared trace/table format; no third-party Python dependencies."""
import json
from pathlib import Path
CLASSES = ('short', 'medium', 'long')

def sites(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]

def oracle(site):
    weights = site['class_bytes']
    return max(range(3), key=lambda i: weights[i]) if sum(weights) else 1

def write_table(path, entries):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(f'{key} {cls}\n' for key, cls in sorted(entries)))
