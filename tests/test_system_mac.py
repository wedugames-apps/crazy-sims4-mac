"""
==============================================================================
Test Suite: Native macOS System Integration & Path Engine
==============================================================================
Verifies:
- macOS path resolution: ~/Documents/Electronic Arts/The Sims 4 & iCloud Drive
- macOS Application Bundle resolution (/Applications/The Sims 4.app)
- iCloud Drive eviction & dateless ghost file detection
- Split Documents detection and safe merging
- Full Disk Access permission verification
- Architecture detection (Apple Silicon & Intel)
"""

import os
import sys
import shutil
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from core.system import SystemIntegration


class TestSystemMac(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.home_dir = os.path.join(self.temp_dir, "Users", "testuser")
        os.makedirs(self.home_dir, exist_ok=True)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_system_architecture(self):
        arch = SystemIntegration.get_system_architecture()
        self.assertTrue(isinstance(arch, str) and len(arch) > 0)

    def test_macos_documents_candidates(self):
        with patch("os.path.expanduser", side_effect=lambda p: p.replace("~", self.home_dir)):
            # Create local Documents and iCloud Documents
            local_docs = os.path.join(self.home_dir, "Documents")
            icloud_docs = os.path.join(self.home_dir, "Library", "Mobile Documents", "com~apple~CloudDocs", "Documents")
            os.makedirs(local_docs, exist_ok=True)
            os.makedirs(icloud_docs, exist_ok=True)

            candidates = SystemIntegration.get_user_documents_folders()
            self.assertIn(local_docs, candidates)
            self.assertIn(icloud_docs, candidates)

    def test_find_sims4_user_folder_scoring(self):
        with patch("os.path.expanduser", side_effect=lambda p: p.replace("~", self.home_dir)):
            local_docs = os.path.join(self.home_dir, "Documents")
            icloud_docs = os.path.join(self.home_dir, "Library", "Mobile Documents", "com~apple~CloudDocs", "Documents")

            # Setup active folder in iCloud with Options.ini
            active_ts4 = os.path.join(icloud_docs, "Electronic Arts", "The Sims 4")
            os.makedirs(os.path.join(active_ts4, "Mods"), exist_ok=True)
            with open(os.path.join(active_ts4, "Options.ini"), "w") as f:
                f.write("[Graphics]\nmetal = 1\n")

            # Setup dormant folder in local Documents without Options.ini
            dormant_ts4 = os.path.join(local_docs, "Electronic Arts", "The Sims 4")
            os.makedirs(dormant_ts4, exist_ok=True)

            with patch.object(SystemIntegration, "get_user_documents_folders", return_value=[local_docs, icloud_docs]):
                found = SystemIntegration.find_sims4_user_folder()
                self.assertEqual(found, active_ts4)

    def test_find_sims4_game_binary(self):
        fake_app = os.path.join(self.temp_dir, "The Sims 4.app")
        fake_exec_dir = os.path.join(fake_app, "Contents", "MacOS")
        os.makedirs(fake_exec_dir, exist_ok=True)
        fake_exec = os.path.join(fake_exec_dir, "The Sims 4")
        with open(fake_exec, "w") as f:
            f.write("#!/bin/sh\n")

        orig_isdir = os.path.isdir
        orig_isfile = os.path.isfile
        with patch("os.path.isdir", side_effect=lambda p: True if p.replace("\\", "/") == "/Applications/The Sims 4.app" else orig_isdir(p)):
            with patch("os.path.isfile", side_effect=lambda p: True if p.replace("\\", "/") == "/Applications/The Sims 4.app/Contents/MacOS/The Sims 4" else orig_isfile(p)):
                found = SystemIntegration.find_sims4_game_binary()
                self.assertEqual(found, "/Applications/The Sims 4.app/Contents/MacOS/The Sims 4")

    def test_icloud_ghost_file_detection(self):
        # 1. File with .icloud extension
        evicted_file = os.path.join(self.temp_dir, ".CoolHair.package.icloud")
        with open(evicted_file, "w") as f:
            f.write("")
        self.assertTrue(SystemIntegration.is_ghost_cloud_file(evicted_file))

        # 2. Zero-byte .package file
        zero_pkg = os.path.join(self.temp_dir, "BrokenPlaceholder.package")
        with open(zero_pkg, "wb") as f:
            pass
        self.assertTrue(SystemIntegration.is_ghost_cloud_file(zero_pkg))

        # 3. Healthy package file
        healthy_pkg = os.path.join(self.temp_dir, "Healthy.package")
        with open(healthy_pkg, "wb") as f:
            f.write(b"DBPF" + b"\x00" * 60)
        self.assertFalse(SystemIntegration.is_ghost_cloud_file(healthy_pkg))

    def test_scan_and_hydrate_ghost_files(self):
        mods_dir = os.path.join(self.temp_dir, "Mods")
        os.makedirs(mods_dir, exist_ok=True)

        g1 = os.path.join(mods_dir, ".Mod1.package.icloud")
        g2 = os.path.join(mods_dir, "Mod2.package")
        h1 = os.path.join(mods_dir, "Mod3.package")

        with open(g1, "wb") as f:
            f.write(b"test data")
        with open(g2, "wb") as f:
            pass  # 0 bytes
        with open(h1, "wb") as f:
            f.write(b"DBPF" + b"\x00" * 32)

        ghosts = SystemIntegration.scan_for_ghost_files(mods_dir)
        self.assertEqual(len(ghosts), 2)
        self.assertIn(g1, ghosts)
        self.assertIn(g2, ghosts)

        hydrated, failed = SystemIntegration.hydrate_all_ghost_files(mods_dir)
        self.assertEqual(hydrated, 2)
        self.assertEqual(failed, 0)

    def test_split_documents_detect_and_merge(self):
        doc1 = os.path.join(self.temp_dir, "DocLocal")
        doc2 = os.path.join(self.temp_dir, "DociCloud")

        ts4_1 = os.path.join(doc1, "Electronic Arts", "The Sims 4")
        ts4_2 = os.path.join(doc2, "Electronic Arts", "The Sims 4")

        os.makedirs(os.path.join(ts4_1, "Mods"), exist_ok=True)
        os.makedirs(os.path.join(ts4_2, "Mods"), exist_ok=True)

        # File in ts4_2 that is missing in ts4_1
        new_mod = os.path.join(ts4_2, "Mods", "ExclusiveMod.package")
        with open(new_mod, "wb") as f:
            f.write(b"DBPF_DATA_12345")

        with patch.object(SystemIntegration, "get_user_documents_folders", return_value=[doc1, doc2]):
            split_info = SystemIntegration.detect_split_documents()
            self.assertIsNotNone(split_info)
            self.assertEqual(split_info["folder_count"], 2)

            copied, msg = SystemIntegration.merge_split_folders(ts4_2, ts4_1)
            self.assertGreaterEqual(copied, 1)
            merged_file = os.path.join(ts4_1, "Mods", "ExclusiveMod.package")
            self.assertTrue(os.path.isfile(merged_file))

    def test_check_permissions(self):
        test_folder = os.path.join(self.temp_dir, "Sims4Folder")
        os.makedirs(test_folder, exist_ok=True)

        perm = SystemIntegration.check_permissions(test_folder)
        self.assertTrue(perm["exists"])
        self.assertTrue(perm["writable"])
        self.assertTrue(perm["full_disk_access_ok"])


if __name__ == "__main__":
    unittest.main()
