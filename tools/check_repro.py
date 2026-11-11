#!/usr/bin/env python3
"""Compare actual BSP bytes from independent output directories."""
import hashlib
import json
from pathlib import Path
from generate import NAMES
ROOT=Path(__file__).resolve().parents[1]
rows=[]
for name in NAMES:
    a=(ROOT/'build/candidate'/f'{name}.bsp').read_bytes()
    b=(ROOT/'build/repro'/f'{name}.bsp').read_bytes()
    if a!=b:
        raise SystemExit(f'nonreproducible map: {name}')
    rows.append({'map':name,'same_bytes_from_clean_output_directory':True,'sha256':hashlib.sha256(a).hexdigest()})
(ROOT/'evidence/reproducibility.json').write_text(json.dumps({'same_pinned_toolchain':True,'results':rows},indent=2)+'\n')
print('Three maps match byte-for-byte.')
