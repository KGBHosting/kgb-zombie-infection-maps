#!/usr/bin/env python3
"""Require source compilation to preserve every non-lighting canonical byte."""
import json
from release_reference import ROOT, compare_rebuild

result = {'source_compilation_required': True, 'canonical_runtime_bytes_not_replaced': True,
          'cross_cpu_rgb_byte_identity_claimed': False,
          'maps': compare_rebuild(ROOT / 'build/candidate')}
(ROOT / 'evidence/rebuild-comparison.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result, indent=2))
