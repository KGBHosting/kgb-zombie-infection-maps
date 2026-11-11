"""Verify immutable first-party release bytes and independently compiled geometry.

Only source-rebuilt RGB lighting may vary across CPUs. Canonical release bytes
have no such exception: every byte is checked against SHA256 and SHA512 pins.
"""
import hashlib
import json
from pathlib import Path
from validate import BSP, require

ROOT = Path(__file__).resolve().parents[1]


def checked_reference(root=ROOT):
    manifest = json.loads((root / 'release/0.1.0.json').read_text())
    runtime = root / 'release/0.1.0/runtime'
    expected = [entry['path'] for entry in manifest['files']]
    actual = [str(p.relative_to(runtime)) for p in runtime.rglob('*') if p.is_file()]
    require(sorted(actual) == sorted(expected), 'canonical runtime file allowlist mismatch')
    files = []
    for entry in manifest['files']:
        path = runtime / entry['path']
        require(not path.is_symlink(), 'canonical runtime symlink forbidden')
        data = path.read_bytes()
        require(len(data) == entry['bytes'], 'canonical runtime size mismatch: ' + entry['path'])
        for algorithm in ('sha256', 'sha512'):
            require(hashlib.new(algorithm, data).hexdigest() == entry[algorithm],
                    'canonical runtime ' + algorithm + ' mismatch: ' + entry['path'])
        files.append((entry['path'], data))
    return manifest, files


def compare_map(rebuilt, canonical):
    # Parse trusted, independently hash-verified reference bounds. A rebuild may
    # change no header, geometry, entity, texture, VIS, collision or padding byte.
    reference = BSP(canonical)
    require(len(rebuilt) == len(canonical), 'rebuilt BSP length mismatch')
    require(rebuilt[:124] == canonical[:124], 'rebuilt BSP header mismatch')
    for index, (offset, length) in enumerate(reference.lumps):
        if index == 8:
            continue
        require(rebuilt[offset:offset + length] == canonical[offset:offset + length],
                'rebuilt non-lighting lump mismatch: ' + str(index))
    offset, length = reference.lumps[8]
    require(rebuilt[:offset] == canonical[:offset] and
            rebuilt[offset + length:] == canonical[offset + length:],
            'rebuilt bytes outside RGB lighting mismatch')
    differences = [abs(a - b) for a, b in
                   zip(rebuilt[offset:offset + length], canonical[offset:offset + length]) if a != b]
    return {'header_identical': True, 'fourteen_non_lighting_lumps_identical': True,
            'all_bytes_outside_rgb_lighting_identical': True,
            'rgb_changed_bytes': len(differences), 'rgb_max_channel_delta': max(differences, default=0),
            'rebuilt_sha256': hashlib.sha256(rebuilt).hexdigest(),
            'canonical_sha256': hashlib.sha256(canonical).hexdigest()}


def compare_rebuild(candidate, root=ROOT):
    _, files = checked_reference(root)
    maps = [(name, data) for name, data in files if name.startswith('maps/')]
    require(sorted(p.name for p in candidate.glob('*.bsp')) ==
            sorted(Path(name).name for name, _ in maps), 'rebuilt BSP file allowlist mismatch')
    return [{'map': Path(name).name, **compare_map((candidate / Path(name).name).read_bytes(), data)}
            for name, data in maps]
