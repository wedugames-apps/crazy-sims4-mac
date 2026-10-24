"""
==============================================================================
Test Suite - Core Engines (DBPF, CASP/GEOM, Texture, Doctor Core, Health Suite)
==============================================================================
Tests deep functionality of core parsing, 3D lag-bomb profiling, Lanczos
downsampling, autonomous diagnostic knowledge base, and health scanner on macOS.
==============================================================================
"""

import os
import shutil
import struct
import tempfile
import unittest
from unittest.mock import patch

from core.dbpf import (
    DBPFPackage,
    DBPFResource,
    STBL,
    TYPE_CASP,
    TYPE_STBL,
    TYPE_PNG,
    TYPE_GEOM,
    get_resource_type_name
)
from core.casp_geom import CaspGeomParser, GeomMeshInfo, FLAG_ALLOW_FOR_RANDOM
from core.texture import TextureProcessor, TextureDownsampler
from core.doctor_core import WeduGamesDoctorCore
from diagnostics.health_suite import MasterHealthSuite, HealthIssue


class TestCoreEnginesMac(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.ts4_folder = os.path.join(self.temp_dir, "The Sims 4")
        self.mods_folder = os.path.join(self.ts4_folder, "Mods")
        self.saves_folder = os.path.join(self.ts4_folder, "saves")
        os.makedirs(self.mods_folder, exist_ok=True)
        os.makedirs(self.saves_folder, exist_ok=True)

        self.ini_path = os.path.join(self.ts4_folder, "Options.ini")
        with open(self.ini_path, "w", encoding="utf-8") as f:
            f.write("metal = 1\nmodsdisabled = 0\nscriptmodsenabled = 1\nvsync = 1\n")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_dbpf_package_lifecycle(self):
        """Tests creating, saving, and reading back a DBPF 2.x package."""
        pkg = DBPFPackage()

        # Add STBL resource
        stbl_entries = [(0x12345678, "Sims 4 Mac Edition"), (0x87654321, "WeduGames Doctor")]
        stbl_bytes = STBL.build(stbl_entries)
        res_stbl = DBPFResource(
            res_type=TYPE_STBL,
            res_group=0x00000000,
            instance_id=0x1122334455667788,
            data=stbl_bytes,
            compressed=True
        )
        pkg.add_resource(res_stbl)

        # Add CASP dummy resource
        dummy_casp = struct.pack("<I", 32) + b"\x00" * 60
        res_casp = DBPFResource(
            res_type=TYPE_CASP,
            res_group=0x80000000,
            instance_id=0x9988776655443322,
            data=dummy_casp,
            compressed=False
        )
        pkg.add_resource(res_casp)

        pkg_path = os.path.join(self.temp_dir, "test_pkg.package")
        pkg.save(pkg_path)

        self.assertTrue(os.path.isfile(pkg_path))
        self.assertGreater(os.path.getsize(pkg_path), 96)

        # Reload and verify
        loaded_pkg = DBPFPackage(pkg_path)
        self.assertEqual(len(loaded_pkg.resources), 2)

        read_stbl_res = loaded_pkg.find_by_type(TYPE_STBL)
        self.assertEqual(len(read_stbl_res), 1)
        parsed_strings = [text for _, text in STBL.parse(read_stbl_res[0].data)]
        self.assertIn("Sims 4 Mac Edition", parsed_strings)
        self.assertIn("WeduGames Doctor", parsed_strings)

    def test_casp_geom_profiling_and_lag_bomb(self):
        """Tests CASP AllowForRandom toggle and GEOM mesh lag bomb detection."""
        # 1. GEOM Normal Mesh (< 30,000 polygons)
        geom_bytes = bytearray()
        geom_bytes.extend(b"GEOM")
        # Version 4, 0 TGIs, shader 0x1234, format 0, 10000 vertices, 30000 indices (10000 tris)
        geom_bytes.extend(struct.pack("<IIIIII", 4, 0, 0x1234, 0, 10000, 30000))
        geom_bytes.extend(b"\x00" * 64)

        mesh_normal = CaspGeomParser.parse_geom(bytes(geom_bytes), tgi="0x015A1849:0:1", lod_level=0)
        self.assertTrue(mesh_normal.is_valid)
        self.assertEqual(mesh_normal.polygon_count, 10000)
        self.assertFalse(mesh_normal.is_lag_bomb)

        # 2. GEOM Lag Bomb (> 30,000 polygons)
        geom_lag = bytearray()
        geom_lag.extend(b"GEOM")
        # 40000 vertices, 120000 indices -> 40000 triangles
        geom_lag.extend(struct.pack("<IIIIII", 4, 0, 0x1234, 0, 40000, 120000))
        geom_lag.extend(b"\x00" * 64)

        mesh_lag = CaspGeomParser.parse_geom(bytes(geom_lag), tgi="0x015A1849:0:2", lod_level=0)
        self.assertTrue(mesh_lag.is_valid)
        self.assertEqual(mesh_lag.polygon_count, 40000)
        self.assertTrue(mesh_lag.is_lag_bomb)

        # 3. CASP AllowForRandom Sanitization
        casp_bytes = bytearray(64)
        struct.pack_into("<I", casp_bytes, 0, 32)
        struct.pack_into("<I", casp_bytes, 16, FLAG_ALLOW_FOR_RANDOM | 0x01)

        casp_info = CaspGeomParser.parse_casp(bytes(casp_bytes))
        self.assertTrue(casp_info.allow_for_random)

        sanitized_bytes = CaspGeomParser.sanitize_casp_for_random(bytes(casp_bytes))
        casp_info_sanitized = CaspGeomParser.parse_casp(sanitized_bytes)
        self.assertFalse(casp_info_sanitized.allow_for_random)

    def test_lanczos_texture_downsampler(self):
        """Tests resizing and downsampling high-res textures via Pillow."""
        from PIL import Image
        import io

        # Create synthetic 4096x4096 texture in memory
        img = Image.new("RGBA", (4096, 4096), color=(255, 0, 0, 255))
        buf = io.BytesIO()
        img.save(buf, format="PNG")
        src_bytes = buf.getvalue()

        # Downsample to 2048
        res_bytes, changed, new_w, new_h = TextureProcessor.downsample_image(src_bytes, max_dim=2048)
        self.assertTrue(changed)
        self.assertEqual(new_w, 2048)
        self.assertEqual(new_h, 2048)
        self.assertLess(len(res_bytes), len(src_bytes))

        with Image.open(io.BytesIO(res_bytes)) as out_img:
            self.assertEqual(out_img.size, (2048, 2048))
            self.assertLessEqual(max(out_img.size), 2048)

    def test_doctor_core_autonomous_diagnosis(self):
        """Tests offline knowledge heuristics for common Sims 4 Mac issues."""
        doctor = WeduGamesDoctorCore()

        # 1. Error 0 (Save error on macOS / iCloud permission lock)
        res_error0 = doctor.diagnose_text("Game shows Error 0 when saving")
        self.assertTrue(res_error0["success"])
        self.assertIn("error code 0", res_error0["diagnosis"].lower())
        self.assertEqual(res_error0["recommended_action"]["action"], "kill_zombies")

        # 2. Metal Shader corruption
        res_metal = doctor.diagnose_text("Sims look pitch black or texture glitch on MacBook")
        self.assertTrue(res_metal["success"])
        self.assertEqual(res_metal["recommended_action"]["action"], "purge_metal_cache")

        # 3. MacBook overheating / battery drain
        res_thermal = doctor.diagnose_text("MacBook gets extremely hot and fans blast when playing")
        self.assertTrue(res_thermal["success"])
        self.assertEqual(res_thermal["recommended_action"]["action"], "apply_fps_limit")

        # 4. iCloud ghost files
        res_icloud = doctor.diagnose_text("Infinite loading screen with icloud ghost files")
        self.assertTrue(res_icloud["success"])
        self.assertEqual(res_icloud["recommended_action"]["action"], "hydrate_icloud")

    def test_master_health_suite_scan_and_autofix(self):
        """Tests 10-point health score evaluation and quarantine backup."""
        # Setup unhealthy environment:
        # A) localthumbcache exists
        cache_p = os.path.join(self.ts4_folder, "localthumbcache.package")
        with open(cache_p, "wb") as f:
            f.write(b"OLD_CACHE_DATA")

        # B) .icloud ghost file in Mods
        ghost_p = os.path.join(self.mods_folder, ".evicted_hair.package.icloud")
        with open(ghost_p, "w") as f:
            f.write("")

        # C) LastException file
        le_p = os.path.join(self.ts4_folder, "lastException.txt")
        with open(le_p, "w", encoding="utf-8") as f:
            f.write("Simulation error: AttributeError: 'NoneType' object has no attribute 'x'\n")

        suite = MasterHealthSuite(self.ts4_folder)
        report = suite.run_health_check()

        self.assertIsInstance(report["health_score"], int)
        self.assertLess(report["health_score"], 100)
        self.assertGreater(len(report["issues"]), 0)

        # Run Auto-Fix All
        fix_results = suite.run_auto_fix_all()
        self.assertGreater(fix_results["actions_count"], 0)

        # Check quarantine directory was created
        quarantine_dir = os.path.join(self.ts4_folder, "Quarantine_WeduGames")
        self.assertTrue(os.path.isdir(quarantine_dir))


if __name__ == "__main__":
    unittest.main()
