#!/bin/sh
# Pinned image or independently recorded source-built CI tools; no server operations.
set -eu
out=${1:-build/candidate}
tool_build=${ERICW_BUILD_DIR:-/opt/build}
mkdir -p "$out"
for map in zm_kgb_courtyard_v1 zm_kgb_depot_v1 zm_kgb_containment_v1; do
  cp "src/$map.map" "$out/$map.map"
  "$tool_build/qbsp/qbsp" -hlbsp -threads 1 -nopercent -noprogress -wadpath assets "$out/$map.map" > "$out/$map.qbsp.log" 2>&1
  test ! -f "$out/$map.pts"
  "$tool_build/vis/vis" -threads 1 -nopercent -noprogress "$out/$map.bsp" > "$out/$map.vis.log" 2>&1
  "$tool_build/light/light" -threads 1 -extra -nopercent -noprogress "$out/$map.bsp" > "$out/$map.light.log" 2>&1
  if grep -Ei 'WARNING|ERROR|LEAK|no visible sides|outside.*map' "$out/$map.qbsp.log" "$out/$map.vis.log" "$out/$map.light.log"; then
    echo 'Map qualification failed: investigate compiler diagnostics.' >&2
    exit 1
  fi
  sha256sum "$out/$map.bsp"
done
