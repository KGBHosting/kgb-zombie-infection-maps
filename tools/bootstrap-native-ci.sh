#!/bin/sh
# Hosted Linux CI only: no apt dependency or prebuilt compiler executable.
set -eu
cd "$(dirname "$0")/.."
for tool in cmake ninja c++ git python3 sudo unshare setpriv; do command -v "$tool" >/dev/null; done
FETCH_ONLY=1 sh tools/bootstrap.sh
root=$(pwd)
# Leave the exact public checkout clean; patch only this isolated build copy.
rm -rf .cache/native-source
cp -a .cache/ericw-tools .cache/native-source
git -C .cache/native-source apply --check "$root/tools/patches/embree-deterministic-device.patch"
git -C .cache/native-source apply "$root/tools/patches/embree-deterministic-device.patch"
deps="$root/.cache/native-deps"
mkdir -p "$deps/embree" "$deps/tbb"
tar -xzf .cache/embree-4.4.0.x86_64.linux.tar.gz -C "$deps/embree"
tar -xzf .cache/oneapi-tbb-2021.11.0-lin.tgz -C "$deps/tbb" --strip-components=1
# An empty network namespace also covers configure, not only map compilation.
# Drop back to the invoking CI uid before touching sources or running compiler code.
offline() { sudo unshare --net -- setpriv --reuid="$(id -u)" --regid="$(id -g)" --init-groups "$@"; }
offline cmake -S .cache/native-source -B .cache/native-build -G Ninja -DCMAKE_BUILD_TYPE=Release "-DCMAKE_PREFIX_PATH=$deps/embree;$deps/tbb" -DDISABLE_TESTS=ON -DDISABLE_DOCS=ON -DENABLE_LIGHTPREVIEW=OFF "-DFETCHCONTENT_SOURCE_DIR_GOOGLETEST=$root/.cache/googletest" -DFETCHCONTENT_FULLY_DISCONNECTED=ON
offline cmake --build .cache/native-build --target qbsp vis light bsputil -j 4
python3 - <<'RECORD'
import hashlib,json,subprocess
from pathlib import Path
record={'route':'source-build-on-hosted-ubuntu24.04','compiler_source_commit':subprocess.check_output(['git','-C','.cache/ericw-tools','rev-parse','HEAD'],text=True).strip(),'network_namespace_for_configure_build_and_map_compile':True,'compiler_patch_sha256':hashlib.sha256(Path('tools/patches/embree-deterministic-device.patch').read_bytes()).hexdigest(),'embree_device_config':'max_isa=avx2,frequency_level=simd128,threads=1','tools':{},'binaries':{}}
for tool in ('cmake','ninja','c++'):
    record['tools'][tool]=subprocess.check_output([tool,'--version'],text=True).splitlines()[0]
for name in ('qbsp','vis','light','bsputil'):
    p=Path('.cache/native-build')/name/name
    record['binaries'][name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
Path('evidence/ci-toolchain.json').write_text(json.dumps(record,indent=2)+'\n')
RECORD
