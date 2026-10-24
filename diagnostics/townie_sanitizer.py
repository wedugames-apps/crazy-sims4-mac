"""
==============================================================================
Crazy The Sims 4 Project - Townie CC Sanitizer (AllowForRandom = 0)
==============================================================================
Prevents random NPC townies from spawning with ridiculous, broken, or immersion-breaking
Custom Content by resetting the AllowForRandom flag to False across CAS packages.
"""

import os
import shutil
from typing import Dict, List, Optional, Tuple
from core.dbpf import DBPFPackage, TYPE_CASP
from core.casp_geom import CaspGeomParser


class TownieSanitizer:
    """Scans and sanitizes CAS CC packages to block random townie assignment."""

    def __init__(self, mods_folder: str):
        self.mods_folder: str = os.path.abspath(mods_folder)

    def scan_townie_cc(self, max_packages: int = 1000) -> List[Dict[str, any]]:
        """
        Scans Mods folder for CAS packages where AllowForRandom is True.
        """
        results = []
        if not os.path.isdir(self.mods_folder):
            return results

        scanned = 0
        for root, _, files in os.walk(self.mods_folder):
            for f in files:
                if f.lower().endswith(".package") and not f.lower().endswith(".disabled"):
                    scanned += 1
                    if scanned > max_packages:
                        break
                    pkg_path = os.path.join(root, f)
                    try:
                        pkg = DBPFPackage(pkg_path)
                        casps = pkg.find_resources(res_type=TYPE_CASP)
                        if not casps:
                            continue

                        random_allowed_count = 0
                        for c in casps:
                            c_info = CaspGeomParser.parse_casp(c.data, tgi=c.tgi)
                            if c_info.allow_for_random:
                                random_allowed_count += 1

                        if random_allowed_count > 0:
                            results.append({
                                "filename": f,
                                "path": pkg_path,
                                "total_casps": len(casps),
                                "random_allowed_count": random_allowed_count
                            })
                    except Exception:
                        pass
            if scanned > max_packages:
                break

        return results

    def sanitize_package(self, package_path: str, create_backup: bool = True) -> Tuple[bool, int]:
        """
        Sanitizes a single package by clearing the AllowForRandom bit on all CASP entries.
        Returns: (success, sanitized_casp_count)
        """
        if not os.path.isfile(package_path):
            return False, 0

        try:
            pkg = DBPFPackage(package_path)
            casps = pkg.find_resources(res_type=TYPE_CASP)
            if not casps:
                return True, 0

            sanitized_count = 0
            for c in casps:
                new_data, modified = CaspGeomParser.sanitize_casp_allow_for_random(c.data)
                if modified:
                    c.data = new_data
                    sanitized_count += 1

            if sanitized_count > 0:
                if create_backup:
                    backup_path = package_path + ".bak_townie"
                    if not os.path.exists(backup_path):
                        shutil.copy2(package_path, backup_path)

                pkg.save_atomic(package_path)

            return True, sanitized_count
        except Exception:
            return False, 0

    def sanitize_all_townie_cc(self, max_packages: int = 1000) -> Tuple[int, int]:
        """
        Scans and sanitizes all CAS CC packages.
        Returns: (sanitized_package_count, total_casps_sanitized)
        """
        targets = self.scan_townie_cc(max_packages=max_packages)
        pkg_count = 0
        total_casps = 0

        for t in targets:
            ok, count = self.sanitize_package(t["path"])
            if ok and count > 0:
                pkg_count += 1
                total_casps += count

        return pkg_count, total_casps
