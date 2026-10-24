"""
==============================================================================
Test Suite: Unified 1-Key macOS Registration & Auto-Unlock System
==============================================================================
Verifies:
- macOS Hardware UUID extraction (ioreg / sysctl / MAC node hash)
- Native macOS cache paths (~/Library/Application Support/EAshare and WeduGames)
- Zero-friction Auto-Unlock via EA Server Dashboard for Mac cache
- Key validation for WG-TS4M-XXXX-XXXX format
- HMAC-SHA256 offline cryptographic signature generation and tamper-proofing
"""

import os
import json
import shutil
import tempfile
import unittest
from unittest.mock import patch

from core.license import MacLicenseManager, BACKUP_SALT


class TestMacLicense(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.eashare_cache = os.path.join(self.temp_dir, "EAshare", "license_cache.json")
        self.wedugames_cache = os.path.join(self.temp_dir, "WeduGames", "license_cache.json")
        self.local_cache = os.path.join(self.temp_dir, "license_cache.json")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_macos_hwid_generation(self):
        hwid = MacLicenseManager.get_macos_hwid()
        self.assertIsInstance(hwid, str)
        self.assertEqual(len(hwid), 16)
        self.assertEqual(hwid, hwid.upper())

    def test_key_format_validation(self):
        # macOS specific key
        self.assertTrue(MacLicenseManager.validate_key_format("WG-TS4M-8899-AABB"))
        # Standard ecosystem key
        self.assertTrue(MacLicenseManager.validate_key_format("WG-TS4-1122-3344"))
        self.assertTrue(MacLicenseManager.validate_key_format("WG-WEDU-ABCD-EFGH"))
        # Invalid keys
        self.assertFalse(MacLicenseManager.validate_key_format(""))
        self.assertFalse(MacLicenseManager.validate_key_format("12345"))

    def test_hmac_sha256_offline_signature_integrity(self):
        key = "WG-TS4M-TEST-1234"
        hwid = "43BAAD0BB81B9042"

        sig = MacLicenseManager.generate_offline_signature(key, hwid)
        self.assertIsInstance(sig, str)
        self.assertEqual(len(sig), 64)  # SHA-256 hex length

        cached_data = {
            "key": key,
            "hwid": hwid,
            "offline_signature": sig,
            "devices": [hwid]
        }

        # Verify authentic match
        self.assertTrue(MacLicenseManager.verify_offline_signature(cached_data, hwid))

        # Tamper check 1: Modified key
        tampered_key = dict(cached_data, key="WG-TS4M-HACK-9999")
        self.assertFalse(MacLicenseManager.verify_offline_signature(tampered_key, hwid))

        # Tamper check 2: Moved to different Mac (different HWID)
        self.assertFalse(MacLicenseManager.verify_offline_signature(cached_data, "DIFFERENT_HWID_001"))

    def test_auto_unlock_via_eashare_dashboard_cache(self):
        """Simulates user already having activated EA Server Dashboard for Mac."""
        os.makedirs(os.path.dirname(self.eashare_cache), exist_ok=True)
        hwid = MacLicenseManager.get_macos_hwid()
        key = "WG-TS4M-AUTO-UNLOCK"
        sig = MacLicenseManager.generate_offline_signature(key, hwid)

        # Write cache as EA Server Dashboard would
        dashboard_data = {
            "key": key,
            "license_key": key,
            "status": "ACTIVE",
            "hwid": hwid,
            "devices": [hwid],
            "offline_signature": sig,
            "products": {"ea_dashboard_mac": True, "smart_dashboard_win": False}
        }
        with open(self.eashare_cache, "w") as f:
            json.dump(dashboard_data, f)

        # Mock cache paths to point to test eashare_cache
        with patch.object(MacLicenseManager, "get_cache_paths", return_value=[self.eashare_cache, self.wedugames_cache]):
            unlocked, msg, cache = MacLicenseManager.check_auto_unlock()
            self.assertTrue(unlocked)
            self.assertIn("Auto-Unlocked", msg)
            self.assertEqual(cache.get("key"), key)

    def test_save_and_load_cached_license(self):
        with patch.object(MacLicenseManager, "get_cache_paths", return_value=[self.eashare_cache, self.wedugames_cache]):
            data = {
                "key": "WG-TS4M-CACHE-TEST",
                "status": "ACTIVE"
            }
            saved = MacLicenseManager.save_cached_license(data)
            self.assertTrue(saved)
            self.assertTrue(os.path.isfile(self.eashare_cache))

            loaded = MacLicenseManager.load_cached_license()
            self.assertIsNotNone(loaded)
            self.assertEqual(loaded.get("key"), "WG-TS4M-CACHE-TEST")
            self.assertIn("offline_signature", loaded)
            self.assertIn("hwid", loaded)


if __name__ == "__main__":
    unittest.main()
