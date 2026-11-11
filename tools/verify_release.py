#!/usr/bin/env python3
"""Require the exact reviewed runtime ZIP, member allowlist and per-file bytes."""
import hashlib,json,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
expected=json.loads((ROOT/'release/0.1.0.json').read_text())
raw=(ROOT/'dist'/expected['archive']['path']).read_bytes()
for algorithm in ('sha256','sha512'):
    assert hashlib.new(algorithm,raw).hexdigest()==expected['archive'][algorithm],algorithm+' archive mismatch'
assert len(raw)==expected['archive']['bytes']
with zipfile.ZipFile(ROOT/'dist'/expected['archive']['path']) as z:
    assert z.namelist()==[f['path'] for f in expected['files']]
    assert z.testzip() is None
    for f in expected['files']:
        d=z.read(f['path']);assert len(d)==f['bytes']
        for algorithm in ('sha256','sha512'):
            assert hashlib.new(algorithm,d).hexdigest()==f[algorithm],f['path']
print('Exact reviewed archive and four allowlisted runtime files verified.')
