"""
==============================================================================
Crazy Doctor for The Sims 4 (macOS Edition) - Unified 1-Key macOS Registration
==============================================================================
Features:
- Native macOS cache paths:
    ~/Library/Application Support/EAshare/license_cache.json
    ~/Library/Application Support/WeduGames/license_cache.json
- Auto-Unlock: Detects existing EA Server Dashboard for Mac activation and
  automatically unlocks Crazy Doctor without re-entering the key.
- Key Validation: Accepts WG-TS4M-XXXX-XXXX (and WG-TS4-XXXX-XXXX) keys,
  validates against Cloudflare R2 (wgtools-repo/user_accounts/),
  binds native macOS Hardware UUID (ioreg / sysctl), and generates
  cryptographic HMAC-SHA256 tamper-proof offline signatures.
"""

import os
import re
import sys
import json
import uuid
import hmac
import shutil
import hashlib
import subprocess
from datetime import datetime, timezone
from typing import Dict, List, Optional, Tuple, Any

# Secret salt and ecosystem constants
BACKUP_SALT = b"WeduGames_TheSims4_CloudSync_v2_2026"
MAX_ALLOWED_DEVICES = 3
COOLDOWN_DAYS = 180

# Cloudflare R2 & Worker Endpoints
R2_BUCKET = "wgtools-repo"
R2_ACCOUNT_ID = "f32fbc8fbbd3a1b3e3a7bbb359c18f48"
SATPAM_R2_URL = "https://wgtools-satpam.wedugamez.workers.dev"
SATPAM_AUTH_HEADER = {"X-Wgames-Auth": "WGTOOLS_VIP_MEMBER_ONLY_2025"}


class MacLicenseManager:
    """Unified 1-Key macOS License and Auto-Unlock Engine."""

    @staticmethod
    def get_cache_paths() -> List[str]:
        """
        Returns persistent cache search paths on macOS in priority order:
        1. ~/Library/Application Support/EAshare/license_cache.json (EA Server Dashboard shared)
        2. ~/Library/Application Support/WeduGames/license_cache.json
        3. ~/.wedugames_license_cache.json
        4. ./license_cache.json (Current directory)
        """
        paths = []
        home = os.path.expanduser("~")

        if sys.platform == "darwin":
            paths.append(os.path.join(home, "Library", "Application Support", "EAshare", "license_cache.json"))
            paths.append(os.path.join(home, "Library", "Application Support", "WeduGames", "license_cache.json"))
        else:
            # Cross-platform support for testing on Windows / Linux
            appdata = os.environ.get("APPDATA") or home
            paths.append(os.path.join(appdata, "EAshare", "license_cache.json"))
            paths.append(os.path.join(appdata, "WeduGames", "license_cache.json"))

        # Fallback hidden user file
        paths.append(os.path.join(home, ".wedugames_license_cache.json"))

        # Local script folder
        try:
            curr_dir = os.path.dirname(os.path.abspath(__file__))
            proj_root = os.path.dirname(curr_dir)
            paths.append(os.path.join(proj_root, "license_cache.json"))
        except Exception:
            pass

        paths.append(os.path.abspath("license_cache.json"))

        # Deduplicate preserving order
        seen = set()
        res = []
        for p in paths:
            norm = os.path.normpath(p)
            if norm not in seen:
                seen.add(norm)
                res.append(norm)
        return res

    @classmethod
    def get_primary_cache_path(cls) -> str:
        """Returns the canonical primary cache path on macOS."""
        paths = cls.get_cache_paths()
        return paths[0]

    # ------------------------------------------------------------------------
    # NATIVE MACOS HARDWARE ID (HWID)
    # ------------------------------------------------------------------------
    @classmethod
    def get_macos_hwid(cls) -> str:
        """
        Extracts native macOS Hardware UUID bound to the Mac's logic board.
        Method 1: ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID
        Method 2: sysctl -n kern.uuid
        Method 3: uuid.getnode() machine MAC address hash fallback
        Returns: 16-character uppercase hex digest.
        """
        if sys.platform == "darwin":
            # 1. ioreg Hardware UUID
            try:
                out = subprocess.check_output(
                    "ioreg -rd1 -c IOPlatformExpertDevice | grep IOPlatformUUID",
                    shell=True, stderr=subprocess.DEVNULL, text=True, timeout=5
                )
                for line in out.splitlines():
                    if "IOPlatformUUID" in line and "=" in line:
                        raw_uuid = line.split("=", 1)[1].replace('"', '').strip()
                        if raw_uuid and len(raw_uuid) >= 16:
                            return hashlib.sha256(raw_uuid.encode("utf-8")).hexdigest()[:16].upper()
            except Exception:
                pass

            # 2. sysctl kern.uuid
            try:
                out = subprocess.check_output(
                    ["sysctl", "-n", "kern.uuid"],
                    stderr=subprocess.DEVNULL, text=True, timeout=5
                ).strip()
                if out and len(out) >= 16:
                    return hashlib.sha256(out.encode("utf-8")).hexdigest()[:16].upper()
            except Exception:
                pass

        elif sys.platform == "win32":
            # Windows fallback for developer testing
            try:
                out = subprocess.check_output(
                    ["powershell", "-NoProfile", "-Command", "(Get-CimInstance -ClassName Win32_ComputerSystemProduct).UUID"],
                    stderr=subprocess.DEVNULL, text=True, timeout=5
                ).strip()
                if out and len(out) > 10 and out.upper() != "NONE":
                    return hashlib.sha256(out.encode()).hexdigest()[:16].upper()
            except Exception:
                pass

        # Universally available node MAC address fallback
        try:
            raw_node = hex(uuid.getnode())
            return hashlib.sha256(raw_node.encode("utf-8")).hexdigest()[:16].upper()
        except Exception:
            return "UNKNOWN_HWID_MAC"

    # ------------------------------------------------------------------------
    # CRYPTOGRAPHIC HMAC-SHA256 SIGNATURE ENGINE
    # ------------------------------------------------------------------------
    @classmethod
    def generate_offline_signature(cls, key: str, hwid: str, expire_at: Optional[str] = None) -> str:
        """
        Generates an HMAC-SHA256 cryptographic signature binding key to this machine's HWID.
        Tampering with the cache file or copying it to another Mac invalidates the signature.
        """
        if not key or not hwid:
            return ""
        raw = f"{key.strip().upper()}|{hwid.strip().upper()}|{str(expire_at)}|WeduGames_VIP_Offline_v2"
        return hmac.new(BACKUP_SALT, raw.encode("utf-8"), hashlib.sha256).hexdigest()

    @classmethod
    def verify_offline_signature(cls, cached_info: Dict[str, Any], current_hwid: str) -> bool:
        """
        Verifies offline cryptographic integrity. Supports both HMAC-SHA256 and legacy SHA256.
        """
        key = cached_info.get("key") or cached_info.get("license_key")
        sig = cached_info.get("offline_signature")
        if not key or not sig:
            return False

        expire_at = cached_info.get("expire_at")
        cur_hwid_u = current_hwid.strip().upper()

        # 1. HMAC-SHA256 for current_hwid
        raw = f"{key.strip().upper()}|{cur_hwid_u}|{str(expire_at)}|WeduGames_VIP_Offline_v2"
        hmac_sig = hmac.new(BACKUP_SALT, raw.encode("utf-8"), hashlib.sha256).hexdigest()
        if hmac.compare_digest(sig, hmac_sig):
            return True

        # 2. Legacy SHA256 (for backward compatibility with early Mac dashboard caches)
        sha_sig = hashlib.sha256(BACKUP_SALT + raw.encode("utf-8")).hexdigest()
        if hmac.compare_digest(sig, sha_sig):
            return True

        return False

    # ------------------------------------------------------------------------
    # CACHE IO
    # ------------------------------------------------------------------------
    @classmethod
    def load_cached_license(cls) -> Optional[Dict[str, Any]]:
        """
        Loads the most recent valid license cache from macOS storage paths.
        """
        paths = cls.get_cache_paths()
        for p in paths:
            if os.path.isfile(p):
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    if isinstance(data, dict) and (data.get("key") or data.get("license_key")):
                        return data
                except Exception:
                    continue
        return None

    @classmethod
    def save_cached_license(cls, data: Dict[str, Any]) -> bool:
        """
        Writes license data to both primary and secondary macOS cache directories.
        """
        paths = cls.get_cache_paths()
        saved = False

        # Ensure hwid and offline signature are set
        hwid = cls.get_macos_hwid()
        data["hwid"] = hwid
        key = data.get("key") or data.get("license_key") or ""
        if key and not data.get("offline_signature"):
            data["offline_signature"] = cls.generate_offline_signature(key, hwid, data.get("expire_at"))

        data["updated_at"] = datetime.now(timezone.utc).isoformat()

        # Write to first 2 primary cache locations (EAshare and WeduGames)
        for p in paths[:2]:
            try:
                os.makedirs(os.path.dirname(p), exist_ok=True)
                with open(p, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                saved = True
            except Exception:
                pass

        # Also write to local project directory fallback
        if len(paths) > 2:
            try:
                fallback_p = paths[-1]
                with open(fallback_p, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)
                saved = True
            except Exception:
                pass

        return saved

    # ------------------------------------------------------------------------
    # AUTO-UNLOCK DETECTION (Zero-Friction for EA Server Dashboard users)
    # ------------------------------------------------------------------------
    @classmethod
    def check_auto_unlock(cls) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Auto-Unlock Detection:
        If the user already activated EA Server Dashboard for Mac,
        Crazy Doctor auto-detects the license cache and unlocks instantly.
        Returns: (is_unlocked, message, license_data)
        """
        cache = cls.load_cached_license()
        if not cache:
            return False, "Belum ada lisensi tersimpan di sistem macOS.", {}

        key = cache.get("key") or cache.get("license_key")
        if not key or len(str(key).strip()) < 8:
            return False, "Format lisensi di cache lokal tidak valid.", {}

        # Check banned status
        if cache.get("banned"):
            return False, "⛔ Lisensi ini telah dinonaktifkan oleh Admin WeduGames.", cache

        # Check expiration
        expire_at = cache.get("expire_at")
        if expire_at:
            try:
                exp_dt = datetime.fromisoformat(str(expire_at).replace("Z", "+00:00"))
                if datetime.now(timezone.utc) > exp_dt:
                    return False, f"⛔ Lisensi telah berakhir pada {expire_at}.", cache
            except Exception:
                pass

        current_hwid = cls.get_macos_hwid()

        # Verify HWID and offline cryptographic signature
        devices = [str(d).strip().upper() for d in cache.get("devices", []) if d]
        cached_hwid = str(cache.get("hwid", "")).strip().upper()
        cur_u = current_hwid.strip().upper()

        hwid_match = (cur_u in devices) or (cur_u == cached_hwid)
        has_signature = bool(cache.get("offline_signature"))

        if has_signature:
            sig_valid = cls.verify_offline_signature(cache, current_hwid)
            if not sig_valid:
                return False, "🔒 Tanda tangan lisensi lokal tidak valid atau telah dimodifikasi.", cache
            is_valid = True
        else:
            if not hwid_match:
                return False, "🔒 Lisensi terikat pada Mac lain. Hubungkan internet untuk aktivasi perangkat ini.", cache
            is_valid = True
            # Upgrade legacy cache with offline HMAC-SHA256 signature
            cache["offline_signature"] = cls.generate_offline_signature(key, current_hwid, expire_at)
            cls.save_cached_license(cache)

        if is_valid:
            # Sync cache to primary location if loaded from secondary
            primary_p = cls.get_primary_cache_path()
            if not os.path.isfile(primary_p):
                cls.save_cached_license(cache)

            msg = "⚡ Auto-Unlocked via WeduGames Mac Ecosystem"
            return True, msg, cache

        return False, "🔒 Lisensi terikat pada Mac lain. Hubungkan internet untuk aktivasi perangkat ini.", cache

    # ------------------------------------------------------------------------
    # CLOUDFLARE R2 ACTIVATION & VALIDATION
    # ------------------------------------------------------------------------
    @classmethod
    def validate_key_format(cls, key: str) -> bool:
        """
        Validates WeduGames license key format (e.g. WG-TS4M-XXXX-XXXX or WG-TS4-XXXX-XXXX).
        """
        if not key:
            return False
        k = key.strip().upper()
        # WG-TS4M-XXXX-XXXX, WG-TS4-XXXX-XXXX, WG-XXXX-XXXX-XXXX
        if re.match(r"^WG-[A-Z0-9]+-[A-Z0-9]+-[A-Z0-9]+", k):
            return True
        if len(k) >= 14 and "-" in k:
            return True
        return False

    @classmethod
    def activate_license(cls, raw_input: str, timeout: int = 6) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validates and activates license key via Cloudflare R2 / Worker satpam:
        1. Formats and hashes identifier (WG-TS4M-XXXX-XXXX).
        2. Queries Cloudflare R2 user_accounts/{key_hash}.json.
        3. Registers this Mac's HWID into the account's allowed devices list (up to 3).
        4. Generates HMAC-SHA256 signature and stores in local macOS cache.
        """
        ident = raw_input.strip()
        if not ident:
            return False, "Silakan masukkan License Key WeduGames Anda.", {}

        key_clean = ident.upper()
        key_hash = hashlib.sha256(key_clean.encode("utf-8")).hexdigest()
        current_hwid = cls.get_macos_hwid()

        # Step 1: Query Cloudflare Worker Satpam
        account_data = None
        try:
            import requests
            worker_url = f"{SATPAM_R2_URL}/user_accounts/{key_hash}.json"
            resp = requests.get(worker_url, headers=SATPAM_AUTH_HEADER, timeout=timeout)
            if resp.status_code == 200:
                account_data = resp.json()
        except Exception:
            pass

        # Step 2: Fallback to local cache verification if network fails
        if not account_data:
            cache = cls.load_cached_license()
            if cache and (cache.get("key") or "").upper() == key_clean:
                unlocked, msg, data = cls.check_auto_unlock()
                if unlocked:
                    return True, "✅ Terhubung secara offline dengan lisensi tersimpan.", data
                return False, msg, {}

            return False, "Gagal menghubungi server lisensi Cloudflare R2. Periksa koneksi internet Anda.", {}

        # Step 3: Validate account status
        if account_data.get("banned"):
            return False, "⛔ Lisensi ini diblokir oleh Admin WeduGames.", {}

        expire_at = account_data.get("expire_at")
        if expire_at:
            try:
                exp_dt = datetime.fromisoformat(str(expire_at).replace("Z", "+00:00"))
                if datetime.now(timezone.utc) > exp_dt:
                    return False, f"⛔ Lisensi telah kedaluwarsa pada {expire_at}.", {}
            except Exception:
                pass

        # Step 4: Device binding
        devices = account_data.get("devices") or []
        devices_upper = [str(d).upper() for d in devices if d]

        if current_hwid.upper() not in devices_upper:
            allowed = account_data.get("allowed_devices", MAX_ALLOWED_DEVICES)
            if len(devices_upper) >= allowed:
                return (
                    False,
                    f"⛔ Kuota perangkat penuh ({len(devices_upper)}/{allowed} Mac/PC terdaftar). "
                    "Hubungi Admin WeduGames untuk reset perangkat.",
                    {}
                )
            devices.append(current_hwid)
            account_data["devices"] = devices

            # Push updated device list to R2 in background or sync
            try:
                import requests
                put_url = f"{SATPAM_R2_URL}/user_accounts/{key_hash}.json"
                account_data["updated_at"] = datetime.now(timezone.utc).isoformat()
                requests.put(put_url, headers=SATPAM_AUTH_HEADER, json=account_data, timeout=5)
            except Exception:
                pass

        # Step 5: Save locally with HMAC-SHA256 offline signature
        sig = cls.generate_offline_signature(key_clean, current_hwid, expire_at)
        account_data["key"] = key_clean
        account_data["license_key"] = key_clean
        account_data["hwid"] = current_hwid
        account_data["offline_signature"] = sig
        account_data["status"] = "ACTIVE"

        cls.save_cached_license(account_data)
        return True, "🎉 Lisensi Crazy Doctor for Mac berhasil diaktifkan!", account_data
