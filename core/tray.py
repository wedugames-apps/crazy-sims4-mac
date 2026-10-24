"""
==============================================================================
Crazy The Sims 4 Project - Tray Inspector & CC Dependency Tracker
==============================================================================
Reads Sims 4 Library items (.trayitem, .householdbinary, .blueprint, .room)
via pure Python protobuf parsing. Extracts CC dependencies and cross-references
against physical .package files in the Mods folder to flag missing/broken CC.
"""

import os
import glob
import struct
import zipfile
from typing import Dict, List, Optional, Set, Tuple

from core.dbpf import DBPFPackage


class ProtobufReader:
    """Pure-Python decoder for Google Protocol Buffers binary streams in Tray files."""

    @staticmethod
    def extract_varints_and_strings(data: bytes) -> Tuple[List[int], List[str]]:
        """Parses varints (including 64-bit resource instance IDs) and UTF-8 strings."""
        pos = 0
        length = len(data)
        varints: List[int] = []
        strings: List[str] = []

        while pos < length:
            try:
                # Read varint tag
                key = 0
                shift = 0
                while True:
                    if pos >= length:
                        return varints, strings
                    b = data[pos]
                    pos += 1
                    key |= (b & 0x7F) << shift
                    if not (b & 0x80):
                        break
                    shift += 7

                wire_type = key & 0x07
                if wire_type == 0:  # Varint
                    val = 0
                    shift = 0
                    while True:
                        if pos >= length:
                            return varints, strings
                        b = data[pos]
                        pos += 1
                        val |= (b & 0x7F) << shift
                        if not (b & 0x80):
                            break
                        shift += 7
                    varints.append(val)

                elif wire_type == 1:  # 64-bit fixed
                    if pos + 8 <= length:
                        val = struct.unpack_from("<Q", data, pos)[0]
                        varints.append(val)
                        pos += 8
                    else:
                        break

                elif wire_type == 2:  # Length-delimited (string or embedded message)
                    s_len = 0
                    shift = 0
                    while True:
                        if pos >= length:
                            return varints, strings
                        b = data[pos]
                        pos += 1
                        s_len |= (b & 0x7F) << shift
                        if not (b & 0x80):
                            break
                        shift += 7

                    if pos + s_len <= length:
                        chunk = data[pos : pos + s_len]
                        pos += s_len
                        try:
                            decoded = chunk.decode("utf-8")
                            if len(decoded) > 1 and all(ord(c) >= 32 or c in "\n\r\t" for c in decoded):
                                strings.append(decoded)
                        except Exception:
                            # Sub-message recursion
                            sub_v, sub_s = ProtobufReader.extract_varints_and_strings(chunk)
                            varints.extend(sub_v)
                            strings.extend(sub_s)
                    else:
                        break

                elif wire_type == 5:  # 32-bit fixed
                    pos += 4
                else:
                    break
            except Exception:
                break

        return varints, strings


class TrayItem:
    """Represents a single Tray item (Household, Lot, or Room)."""

    def __init__(self, trayitem_path: str):
        self.trayitem_path: str = trayitem_path
        self.file_stem: str = os.path.splitext(os.path.basename(trayitem_path))[0]
        self.tray_dir: str = os.path.dirname(trayitem_path)

        self.name: str = "Unknown Library Item"
        self.item_type: str = "Unknown"  # Household, Lot, Room
        self.creator_name: str = ""
        self.description: str = ""
        self.companion_files: List[str] = [trayitem_path]
        self.thumbnail_files: List[str] = []
        self.referenced_instance_ids: Set[int] = set()

        self._load_trayitem_data()
        self._find_companion_files()

    def _load_trayitem_data(self):
        try:
            with open(self.trayitem_path, "rb") as f:
                data = f.read()
            varints, strings = ProtobufReader.extract_varints_and_strings(data)

            # Heuristics for name, creator, description
            clean_strings = [s.strip() for s in strings if s.strip() and not s.startswith("http")]
            if clean_strings:
                self.name = clean_strings[0]
                if len(clean_strings) > 1:
                    self.creator_name = clean_strings[1]
                if len(clean_strings) > 2:
                    self.description = clean_strings[2]

            # Collect 64-bit instance IDs (ignoring zero and small integers)
            for v in varints:
                if v > 0x10000000:
                    self.referenced_instance_ids.add(v)
        except Exception:
            pass

    def _find_companion_files(self):
        try:
            pattern = os.path.join(self.tray_dir, f"{self.file_stem}.*")
            for f in glob.glob(pattern):
                if f != self.trayitem_path and f not in self.companion_files:
                    self.companion_files.append(f)
                    ext = os.path.splitext(f)[1].lower()
                    if ext in (".hhi", ".bpi", ".sgi", ".rmi"):
                        self.thumbnail_files.append(f)
                    elif ext == ".householdbinary":
                        self.item_type = "Household (Sims)"
                        self._extract_dependencies_from_file(f)
                    elif ext == ".blueprint":
                        self.item_type = "Lot (Building)"
                        self._extract_dependencies_from_file(f)
                    elif ext == ".room":
                        self.item_type = "Room"
                        self._extract_dependencies_from_file(f)
        except Exception:
            pass

        if self.item_type == "Unknown":
            if any(f.endswith(".householdbinary") for f in self.companion_files):
                self.item_type = "Household (Sims)"
            elif any(f.endswith(".blueprint") for f in self.companion_files):
                self.item_type = "Lot (Building)"
            elif any(f.endswith(".room") for f in self.companion_files):
                self.item_type = "Room"

    def _extract_dependencies_from_file(self, file_path: str):
        try:
            with open(file_path, "rb") as f:
                data = f.read()
            varints, _ = ProtobufReader.extract_varints_and_strings(data)
            for v in varints:
                if v > 0x10000000:
                    self.referenced_instance_ids.add(v)
        except Exception:
            pass


class TrayInspector:
    """Scans and analyzes Tray items and their CC dependencies."""

    def __init__(self, tray_folder: str, mods_folder: Optional[str] = None):
        self.tray_folder: str = os.path.abspath(tray_folder)
        self.mods_folder: Optional[str] = os.path.abspath(mods_folder) if mods_folder else None
        self.items: List[TrayItem] = []
        self.mod_index: Dict[int, str] = {}  # instance_id -> package_path

    def scan_tray_items(self) -> List[TrayItem]:
        """Scans all .trayitem files in the Tray folder."""
        self.items.clear()
        if not os.path.isdir(self.tray_folder):
            return self.items

        for fname in os.listdir(self.tray_folder):
            if fname.lower().endswith(".trayitem"):
                full_path = os.path.join(self.tray_folder, fname)
                try:
                    item = TrayItem(full_path)
                    self.items.append(item)
                except Exception:
                    pass

        return self.items

    def build_mods_index(self, max_packages: int = 1000) -> Dict[int, str]:
        """
        Indexes all package resources in the Mods folder.
        Maps 64-bit instance IDs to their source .package file path.
        """
        self.mod_index.clear()
        if not self.mods_folder or not os.path.isdir(self.mods_folder):
            return self.mod_index

        pkg_count = 0
        for root, _, files in os.walk(self.mods_folder):
            for file in files:
                if file.lower().endswith(".package"):
                    pkg_count += 1
                    if pkg_count > max_packages:
                        break
                    pkg_path = os.path.join(root, file)
                    try:
                        # Quick index reading
                        pkg = DBPFPackage(pkg_path)
                        for r in pkg.resources:
                            self.mod_index[r.instance_id] = pkg_path
                    except Exception:
                        pass
            if pkg_count > max_packages:
                break

        return self.mod_index

    def check_item_dependencies(self, item: TrayItem) -> Dict[str, any]:
        """
        Cross-references a TrayItem's referenced instance IDs against the indexed Mods.
        Returns found CC files and missing CC IDs.
        """
        found_packages: Set[str] = set()
        matched_instances: Set[int] = set()
        missing_instances: Set[int] = set()

        for inst in item.referenced_instance_ids:
            if inst in self.mod_index:
                pkg_path = self.mod_index[inst]
                found_packages.add(pkg_path)
                matched_instances.add(inst)
            else:
                # High 32 bits check: custom content usually has non-trivial instance hashes
                # Base game resources usually have specific EA group/instance patterns
                missing_instances.add(inst)

        return {
            "item_name": item.name,
            "total_references": len(item.referenced_instance_ids),
            "found_cc_packages": list(found_packages),
            "found_cc_count": len(found_packages),
            "missing_instance_count": len(missing_instances),
            "missing_instances": list(missing_instances)
        }

    def export_tray_bundle(self, item: TrayItem, output_zip: str) -> bool:
        """
        Exports a TrayItem, its companion files, and all matched CC packages
        into a single distributable .zip archive.
        """
        dep_info = self.check_item_dependencies(item)
        found_pkgs = dep_info["found_cc_packages"]

        os.makedirs(os.path.dirname(os.path.abspath(output_zip)), exist_ok=True)
        try:
            with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                # Add Tray files
                for f in item.companion_files:
                    if os.path.exists(f):
                        arcname = os.path.join("Tray", os.path.basename(f))
                        zf.write(f, arcname)

                # Add Mods files
                for pkg in found_pkgs:
                    if os.path.exists(pkg):
                        arcname = os.path.join("Mods", os.path.basename(pkg))
                        zf.write(pkg, arcname)

            return True
        except Exception:
            return False
