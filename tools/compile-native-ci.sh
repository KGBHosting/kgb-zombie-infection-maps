#!/bin/sh
# Hosted Linux CI: run the source-built tools offline with the frozen flags.
set -eu
case "${1:-}" in build/candidate|build/repro) ;; *) echo 'Expected fixed CI output directory' >&2; exit 1 ;; esac
root=$(pwd)
sudo unshare --net -- env "ERICW_BUILD_DIR=$root/.cache/native-build" "LD_LIBRARY_PATH=$root/.cache/native-deps/embree/lib:$root/.cache/native-deps/tbb/lib" sh tools/compile.sh "$1"
