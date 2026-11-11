"""Test-only local mutation controls; no server or canonical file is changed."""
from pathlib import Path
import shutil
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from release_reference import checked_reference, compare_map, compare_rebuild
from validate import BSP


class CanonicalReleaseChecks(unittest.TestCase):
    def setUp(self):
        self.canonical = (ROOT / 'release/0.1.0/runtime/maps/zm_kgb_courtyard_v1.bsp').read_bytes()
        self.bsp = BSP(self.canonical)

    def copied_reference(self, directory):
        root = Path(directory)
        shutil.copytree(ROOT / 'release/0.1.0', root / 'release/0.1.0')
        shutil.copyfile(ROOT / 'release/0.1.0.json', root / 'release/0.1.0.json')
        return root

    def test_actual_canonical_files_are_pinned_and_compiled_geometry_matches(self):
        _, files = checked_reference()
        self.assertEqual(len(files), 4)
        results = compare_rebuild(ROOT / 'build/candidate')
        self.assertEqual(len(results), 3)
        self.assertTrue(all(r['fourteen_non_lighting_lumps_identical'] for r in results))

    def test_only_rebuilt_rgb_variation_is_allowed_and_quantified(self):
        data = bytearray(self.canonical)
        offset, _ = self.bsp.lumps[8]
        data[offset] ^= 1
        result = compare_map(bytes(data), self.canonical)
        self.assertEqual((result['rgb_changed_bytes'], result['rgb_max_channel_delta']), (1, 1))
        self.assertNotEqual(result['rebuilt_sha256'], result['canonical_sha256'])

    def test_each_non_lighting_source_lump_including_geometry_is_rejected(self):
        # Every source-produced entity/geometry/texture/VIS/collision lump is
        # independently controlled, not merely a convenient header-field check.
        for index, (offset, length) in enumerate(self.bsp.lumps):
            if index == 8:
                continue
            with self.subTest(lump=index):
                self.assertGreater(length, 0)
                data = bytearray(self.canonical)
                data[offset] ^= 1
                with self.assertRaisesRegex(ValueError, 'non-lighting lump'):
                    compare_map(bytes(data), self.canonical)

    def test_source_header_change_is_rejected(self):
        data = bytearray(self.canonical)
        struct.pack_into('<i', data, 0, 29)
        with self.assertRaisesRegex(ValueError, 'header'):
            compare_map(bytes(data), self.canonical)

    def test_source_extra_bytes_are_rejected(self):
        with self.assertRaisesRegex(ValueError, 'length'):
            compare_map(self.canonical + b'\0', self.canonical)

    def test_canonical_runtime_mutations_are_rejected_including_rgb(self):
        _, files = checked_reference()
        for name, _ in files:
            with self.subTest(runtime_file=name), tempfile.TemporaryDirectory() as td:
                root = self.copied_reference(td)
                path = root / 'release/0.1.0/runtime' / name
                data = bytearray(path.read_bytes())
                # RGB is permitted only in independent rebuilds, never in the
                # authoritative runtime. Also cover the dedicated cycle bytes.
                offset = BSP(data).lumps[8][0] if name.endswith('.bsp') else 0
                data[offset] ^= 1
                path.write_bytes(data)
                with self.assertRaisesRegex(ValueError, 'canonical runtime sha256'):
                    checked_reference(root)

    def test_unowned_canonical_file_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            root = self.copied_reference(td)
            (root / 'release/0.1.0/runtime/unowned.cfg').write_text('test-only mutation\n')
            with self.assertRaisesRegex(ValueError, 'allowlist'):
                checked_reference(root)

    def test_missing_source_map_is_rejected(self):
        with tempfile.TemporaryDirectory() as td:
            with self.assertRaisesRegex(ValueError, 'BSP file allowlist'):
                compare_rebuild(Path(td))


if __name__ == '__main__':
    unittest.main()
