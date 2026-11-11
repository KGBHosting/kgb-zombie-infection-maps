#!/usr/bin/env python3
"""Package hash-verified first-party canonical release bytes, never CPU variants.

CI independently source-compiles twice and compares every non-lighting byte
before this step. Rebuilds do not replace the live-qualified release authority.
"""
import hashlib
import json
from pathlib import Path
import zipfile
from generate import NAMES
from validate import inspect
from release_reference import checked_reference

ROOT=Path(__file__).resolve().parents[1]
_, files=checked_reference()
cycle=files[0][1]
assert files[0][0]=='kgb_zombie_infection_mapcycle.txt'
assert cycle==''.join(name+'\n' for name in NAMES).encode()
for name in NAMES:
    inspect(ROOT/'release/0.1.0/runtime/maps'/f'{name}.bsp',navigation=False)
archive=ROOT/'dist/kgb-zombie-infection-maps-0.1.0.zip'
archive.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(archive,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=9) as z:
    for name,data in files:
        info=zipfile.ZipInfo(name,date_time=(1980,1,1,0,0,0));info.create_system=3
        info.external_attr=0o100644<<16;info.compress_type=zipfile.ZIP_DEFLATED
        z.writestr(info,data,compress_type=zipfile.ZIP_DEFLATED,compresslevel=9)
with zipfile.ZipFile(archive) as z:
    assert z.namelist()==[n for n,_ in files]
    assert z.testzip() is None
    for name,data in files:
        assert z.read(name)==data
manifest={'pack':'kgb-zombie-infection-maps','candidate_version':'0.1.0','license':'CC0-1.0','release_stage':'development-candidate','full_live_qualification':'pending',
 'files':[{'path':name,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest(),'sha512':hashlib.sha512(data).hexdigest()} for name,data in files]}
raw=archive.read_bytes()
manifest['archive']={'path':archive.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest(),'sha512':hashlib.sha512(raw).hexdigest()}
(ROOT/'dist/manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
(ROOT/'dist/kgb_zombie_infection_mapcycle.txt').write_bytes(cycle)
print(json.dumps(manifest,indent=2))
