"""
==============================================================================
Test Suite: Apple Metal API Graphics & Shader Diagnostic Engine
==============================================================================
Verifies:
- macOS Options.ini parser & Apple Metal API configuration
- Metal shader cache scanning & purging (~/Library/Caches/com.ea.TheSims4/)
- localthumbcache & user thumbnail purging
- MacBook & iMac thermal limiter (60Hz Retina & 120Hz ProMotion)
"""

import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from diagnostics.graphics import GraphicsDiagnostic


class TestMetalGraphics(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.ts4_user_dir = os.path.join(self.temp_dir, "The Sims 4")
        os.makedirs(self.ts4_user_dir, exist_ok=True)
        self.diag = GraphicsDiagnostic(self.ts4_user_dir)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_metal_api_mode_detection(self):
        ini_file = os.path.join(self.ts4_user_dir, "Options.ini")
        with open(ini_file, "w") as f:
            f.write("[Graphics]\nmetal = 1\nvsync = 1\n")

        mode_info = self.diag.get_graphics_mode()
        self.assertTrue(mode_info["is_metal"])
        self.assertEqual(mode_info["raw_setting"], 1)
        self.assertTrue(mode_info["vsync_enabled"])
        self.assertIn("Metal", mode_info["mode"])

    def test_set_metal_mode(self):
        ok, msg = self.diag.set_metal_mode(enable_metal=True)
        self.assertTrue(ok)

        ini_file = os.path.join(self.ts4_user_dir, "Options.ini")
        self.assertTrue(os.path.isfile(ini_file))
        with open(ini_file, "r") as f:
            content = f.read()
        self.assertIn("metal = 1", content)

    def test_metal_shader_and_user_cache_inspection(self):
        # 1. Create user cache items
        thumb = os.path.join(self.ts4_user_dir, "localthumbcache.package")
        with open(thumb, "wb") as f:
            f.write(b"THUMBNAIL_CACHE_DATA_BYTES")

        cache_dir = os.path.join(self.ts4_user_dir, "cache")
        os.makedirs(cache_dir, exist_ok=True)
        with open(os.path.join(cache_dir, "temp_data.dat"), "wb") as f:
            f.write(b"TEMP_CACHE_BYTES")

        # 2. Create mock Metal shader cache in fake ~/Library/Caches/com.ea.TheSims4
        fake_metal_cache = os.path.join(self.temp_dir, "Caches", "com.ea.TheSims4")
        os.makedirs(fake_metal_cache, exist_ok=True)
        with open(os.path.join(fake_metal_cache, "metal_pipeline.cache"), "wb") as f:
            f.write(b"COMPILED_METAL_SHADERS_DATA")

        self.diag.macos_metal_cache_dirs = [fake_metal_cache]

        items = self.diag.inspect_cache_items()
        item_paths = [i["path"] for i in items]

        self.assertIn(thumb, item_paths)
        self.assertIn(cache_dir, item_paths)
        self.assertIn(fake_metal_cache, item_paths)

        # 3. Purge caches
        purged_count, freed_bytes = self.diag.purge_cache()
        self.assertGreaterEqual(purged_count, 3)
        self.assertGreater(freed_bytes, 0)

        # Verify files were removed
        self.assertFalse(os.path.exists(thumb))
        self.assertFalse(os.path.exists(cache_dir))
        self.assertFalse(os.path.exists(fake_metal_cache))

    def test_fps_limiter_thermal_protection_60fps(self):
        # Default uncapped
        fps_info = self.diag.inspect_fps_limit()
        self.assertTrue(fps_info["overheating_risk"])

        # Apply 60 FPS cap
        ok, msg = self.diag.apply_fps_limiter(target_fps=60, force_vsync=True)
        self.assertTrue(ok)

        # Verify GraphicsRules.sgr and Options.ini
        rules_file = os.path.join(self.ts4_user_dir, "ConfigOverride", "GraphicsRules.sgr")
        self.assertTrue(os.path.isfile(rules_file))
        with open(rules_file, "r") as f:
            rules = f.read()
        self.assertIn("setprop maxFPS 60", rules)

        fps_info_after = self.diag.inspect_fps_limit()
        self.assertFalse(fps_info_after["overheating_risk"])
        self.assertEqual(fps_info_after["max_fps_rule"], 60)
        self.assertTrue(fps_info_after["vsync_enabled"])

    def test_fps_limiter_promotion_120fps(self):
        # Apply 120 FPS cap for MacBook Pro Liquid Retina XDR ProMotion
        ok, msg = self.diag.apply_fps_limiter(target_fps=120, force_vsync=True)
        self.assertTrue(ok)

        rules_file = os.path.join(self.ts4_user_dir, "ConfigOverride", "GraphicsRules.sgr")
        with open(rules_file, "r") as f:
            rules = f.read()
        self.assertIn("setprop maxFPS 120", rules)

        fps_info = self.diag.inspect_fps_limit()
        self.assertEqual(fps_info["max_fps_rule"], 120)
        self.assertIn("ProMotion", fps_info["display_profile"])


if __name__ == "__main__":
    unittest.main()
