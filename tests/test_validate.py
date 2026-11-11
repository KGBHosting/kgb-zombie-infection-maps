"""Negative controls mutate local map copies in memory; never server files."""
import importlib.util
from pathlib import Path
import struct
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('validator',ROOT/'tools/validate.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)

class CompiledMapChecks(unittest.TestCase):
    def setUp(self):
        self.data=bytearray((ROOT/'build/candidate/zm_kgb_courtyard_v1.bsp').read_bytes())
    def inspect_copy(self,data):
        with tempfile.TemporaryDirectory() as td:
            p=Path(td)/'candidate.bsp';p.write_bytes(data)
            return v.inspect(p,navigation=False)
    def test_three_actual_compiled_maps(self):
        for p in (ROOT/'build/candidate').glob('*.bsp'):
            with self.subTest(map=p.name):
                r=v.inspect(p,navigation=False)
                self.assertEqual((r['ct_spawns'],r['t_spawns']),(32,32))
    def test_wrong_bsp_version_rejected(self):
        struct.pack_into('<i',self.data,0,29)
        with self.assertRaisesRegex(ValueError,'BSP30'):
            self.inspect_copy(self.data)
    def test_external_texture_rejected(self):
        o,_=struct.unpack_from('<ii',self.data,4+8*2)
        first=struct.unpack_from('<i',self.data,o+4)[0]
        struct.pack_into('<i',self.data,o+first+24,0)
        with self.assertRaisesRegex(ValueError,'external or truncated'):
            self.inspect_copy(self.data)
    def test_overlapping_spawns_rejected(self):
        # Both are same-width fields; preserve all BSP offsets and string length.
        self.assertIn(b'"origin" "-240 832 40"',self.data)
        mutated=self.data.replace(b'"origin" "-240 832 40"',b'"origin" "-336 832 40"',1)
        with self.assertRaisesRegex(ValueError,'origins overlap'):
            self.inspect_copy(mutated)
    def test_solid_spawn_rejected(self):
        mutated=self.data.replace(b'"origin" "-336 832 40"',b'"origin" "-336 832 04"',1)
        with self.assertRaisesRegex(ValueError,'spawn blocked'):
            self.inspect_copy(mutated)
    def test_objective_or_unknown_entity_rejected(self):
        self.assertIn(b'"classname" "light"',self.data)
        mutated=self.data.replace(b'"classname" "light"',b'"classname" "timer"',1)
        with self.assertRaisesRegex(ValueError,'entity class'):
            self.inspect_copy(mutated)
    def test_missing_lighting_rejected(self):
        struct.pack_into('<i',self.data,4+8*8+4,0)
        with self.assertRaisesRegex(ValueError,'RGB lighting'):
            self.inspect_copy(self.data)
    def test_out_of_bounds_lump_rejected(self):
        struct.pack_into('<i',self.data,4+8*8,len(self.data)+1)
        with self.assertRaisesRegex(ValueError,'lump bounds'):
            self.inspect_copy(self.data)

if __name__=='__main__':
    unittest.main()
