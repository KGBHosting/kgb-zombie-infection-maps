#!/bin/sh
set -eu
for map in zm_kgb_courtyard_v1 zm_kgb_depot_v1 zm_kgb_containment_v1; do
  /opt/build/bsputil/bsputil -check "build/candidate/$map.bsp" > "evidence/$map.bsputil-check.log" 2>&1
  /opt/build/bsputil/bsputil -svg "build/candidate/$map.bsp" > "evidence/$map.svg.log" 2>&1
  cp "build/candidate/$map.svg" "evidence/$map.compiled-preview.svg"
done
