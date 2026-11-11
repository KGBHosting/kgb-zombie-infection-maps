#!/bin/sh
# BOUNDED BUILD DIAGNOSTIC ONLY. Four documented ISA choices, no BSP byte edits.
# The release hash gate remains failing until a separately reviewed fix passes.
set -eu
root=$(pwd)
offline() { sudo unshare --net -- setpriv --reuid="$(id -u)" --regid="$(id -g)" --init-groups "$@"; }
cp .cache/native-source/light/trace_embree.cc .cache/diagnostic-original-trace.cc
mkdir -p build/isa-probe
for isa in sse2 sse4.2 avx avx2; do
  export PROBE_ISA="$isa"
  python3 - <<'PY'
from pathlib import Path
import os
s=Path('.cache/diagnostic-original-trace.cc').read_text()
old='device = rtcNewDevice("max_isa=avx2,frequency_level=simd128,threads=1");'
assert s.count(old)==1
isa=os.environ['PROBE_ISA'];assert isa in ('sse2','sse4.2','avx','avx2')
Path('.cache/native-source/light/trace_embree.cc').write_text(s.replace(old,'device = rtcNewDevice("isa='+isa+',frequency_level=simd128,threads=1");'))
PY
  out="build/isa-probe/$isa"
  mkdir -p "$out"
  offline cmake --build .cache/native-build --target light -j 2 > "$out/compiler.log" 2>&1
  for map in zm_kgb_courtyard_v1 zm_kgb_depot_v1 zm_kgb_containment_v1; do
    cp "build/candidate/$map.bsp" "build/candidate/$map.texinfo.json" "build/candidate/$map.content.json" "$out/"
    offline env "LD_LIBRARY_PATH=$root/.cache/native-deps/embree/lib:$root/.cache/native-deps/tbb/lib" .cache/native-build/light/light -threads 1 -extra -nopercent -noprogress "$out/$map.bsp" > "$out/$map.light.log" 2>&1
  done
  python3 - <<'PY'
from pathlib import Path
import hashlib,json,os,struct
isa=os.environ['PROBE_ISA'];rows=[]
expected={row['path']:row for row in json.loads(Path('release/0.1.0.json').read_text())['files']}
for p in Path('build/candidate').glob('*.bsp'):
 a=p.read_bytes();b=(Path('build/isa-probe')/isa/p.name).read_bytes();lumps=[]
 for i in range(15):
  ao,an=struct.unpack_from('<ii',a,4+i*8);bo,bn=struct.unpack_from('<ii',b,4+i*8)
  if a[ao:ao+an]!=b[bo:bo+bn] or (ao,an)!=(bo,bn):lumps.append(i)
 sha=hashlib.sha256(b).hexdigest()
 rows.append({'map':p.name,'bytes':len(b),'sha256':sha,'sha512':hashlib.sha512(b).hexdigest(),'matches_frozen_release':sha==expected['maps/'+p.name]['sha256'],'different_lumps_from_primary_build':lumps})
record={'diagnostic_only':True,'isa':isa,'frequency_level':'simd128','threads':1,'maps':rows}
(Path('build/isa-probe')/isa/'result.json').write_text(json.dumps(record,indent=2)+'\n')
print(json.dumps(record))
PY
done
# The diagnostic source/binary is not a release compiler or runtime artifact.
