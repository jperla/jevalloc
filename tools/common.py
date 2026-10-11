"""Shared trace/table format; no third-party Python dependencies."""
import json
from pathlib import Path
CLASSES = ('transient', 'permanent')
CLASS_SCHEMA = 'transient-permanent-v1'

def sites(path):
    with open(path) as f:
        return [json.loads(line) for line in f if line.strip()]

def class_bytes(site, short_bytes=None, permanent_percent=50):
    if site.get('class_schema') != CLASS_SCHEMA:
        raise ValueError('Legacy trace: keep archived; retrace for transient/permanent results')
    if short_bytes is not None:
        if short_bytes <= 0: raise ValueError('short_bytes must be positive')
        if short_bytes == site.get('short_bytes'):
            return site['fixed_s_class_bytes']
        if short_bytes & (short_bytes-1):
            raise ValueError('Retrace for a non-power-of-two threshold; histogram is insufficient')
        short = sum(site['lifetime_histogram_bytes'][:short_bytes.bit_length()])
        return [short, site['bytes']-short]
    if permanent_percent == 'never': permanent = site['never_freed_bytes']
    elif str(permanent_percent) in ('25', '50', '90'):
        permanent = site['permanent_bytes_by_percent'][str(permanent_percent)]
    else: raise ValueError('permanent_percent must be 25, 50, 90 or never')
    return [site['bytes']-permanent, permanent]

def oracle(site, short_bytes=None, permanent_percent=50):
    weights = class_bytes(site, short_bytes, permanent_percent)
    return 0 if weights[0] >= weights[1] else 1

def write_table(path, entries):
    entries = list(entries)
    if any(cls not in (0, 1) for _, cls in entries): raise ValueError('class must be 0 or 1')
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(''.join(f'{key} {cls}\n' for key, cls in sorted(entries)))
