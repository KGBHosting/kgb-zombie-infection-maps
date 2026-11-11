#!/bin/sh
# Fetch only public pinned build tools. They are never runtime map payloads.
set -eu
cd "$(dirname "$0")/.."
mkdir -p .cache
if [ ! -d .cache/ericw-tools/.git ]; then
  git clone --filter=blob:none --recurse-submodules --shallow-submodules --branch 2.0.0-alpha11 --depth 1 https://github.com/ericwa/ericw-tools.git .cache/ericw-tools
fi
test "$(git -C .cache/ericw-tools rev-parse HEAD)" = c243aa348c9e5a1838bb69cf6c3ff20bebd94a8a
git -C .cache/ericw-tools diff --quiet
git -C .cache/ericw-tools diff --cached --quiet
python3 - <<'PY'
import json,subprocess
from pathlib import Path
meta=json.loads(Path('tools/toolchain.json').read_text())
for expected in meta['compiler']['submodule_status']:
    commit,path,*_=expected.strip().split()
    actual=subprocess.check_output(['git','-C','.cache/ericw-tools/'+path,'rev-parse','HEAD'],text=True).strip()
    assert actual==commit,(path,actual,commit)
PY
if [ ! -f .cache/embree-4.4.0.x86_64.linux.tar.gz ]; then
  curl --fail --location --silent --show-error https://github.com/RenderKit/embree/releases/download/v4.4.0/embree-4.4.0.x86_64.linux.tar.gz -o .cache/embree-4.4.0.x86_64.linux.tar.gz
fi
if [ ! -f .cache/oneapi-tbb-2021.11.0-lin.tgz ]; then
  curl --fail --location --silent --show-error https://github.com/uxlfoundation/oneTBB/releases/download/v2021.11.0/oneapi-tbb-2021.11.0-lin.tgz -o .cache/oneapi-tbb-2021.11.0-lin.tgz
fi
# Verify public dependency bytes before either source-build route uses them.
python3 - <<'CHECKSUMS'
import hashlib,json
from pathlib import Path
for dependency in json.loads(Path('tools/toolchain.json').read_text())['dependencies']:
    archive=Path('.cache')/dependency['url'].rsplit('/',1)[1]
    assert hashlib.sha256(archive.read_bytes()).hexdigest()==dependency['sha256'],dependency['name']
CHECKSUMS
if [ "${FETCH_ONLY:-0}" = 1 ]; then exit 0; fi
docker build --platform linux/amd64 -f tools/Dockerfile -t kgb-zi-map-tools:alpha11 .
