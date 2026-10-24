"""
==============================================================================
Crazy The Sims 4 Project - Save Game Archivist & Rollback Engine
==============================================================================
Manages Sims 4 save slots (Slot_XXXXXXXX.save) and rolling backups (.ver0 - .ver4).
Provides:
- Slot integrity & corruption analysis
- Safe 1-Click Rollback with pre-restore safety checkpoint
- Point-in-time Snapshot archiving with JSON manifests
- Clean-up of stale rolling backups to reclaim gigabytes of disk space
"""

import os
import re
import json
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Tuple


class SaveSlotInfo:
    """Represents a single save game slot and its rolling backup versions."""

    def __init__(self, slot_hex: str, slot_dec: int, is_autosave: bool = False):
        self.slot_hex: str = slot_hex.upper()
        self.slot_dec: int = slot_dec
        self.is_autosave: bool = is_autosave
        self.main_file: Optional[str] = None
        self.main_size: int = 0
        self.main_mtime: float = 0.0
        self.versions: List[Dict[str, any]] = []  # [{ver, path, filename, size, mtime}]
        self.total_size: int = 0
        self.is_corrupted: bool = False
        self.corruption_reason: Optional[str] = None

    @property
    def last_played_str(self) -> str:
        if self.main_mtime > 0:
            return datetime.fromtimestamp(self.main_mtime).strftime("%Y-%m-%d %H:%M:%S")
        return "Unknown"

    def __repr__(self) -> str:
        return f"<SaveSlot Slot={self.slot_hex} (Dec {self.slot_dec}) Versions={len(self.versions)}>"


class SaveArchivist:
    """Engine for save game scanning, snapshot creation, and safe rollback."""

    def __init__(self, saves_folder: str, archive_folder: Optional[str] = None):
        self.saves_folder: str = os.path.abspath(saves_folder)
        self.archive_folder: str = (
            os.path.abspath(archive_folder)
            if archive_folder
            else os.path.join(self.saves_folder, "Saves_Archive")
        )
        self.slots: Dict[str, SaveSlotInfo] = {}

    def scan_slots(self) -> Dict[str, SaveSlotInfo]:
        """Scans the saves/ directory for all slots and rolling backups."""
        self.slots.clear()
        if not os.path.isdir(self.saves_folder):
            return self.slots

        pattern = re.compile(r"^slot_([0-9a-fA-F]+)\.save(?:\.ver(\d+))?$", re.IGNORECASE)

        for fname in os.listdir(self.saves_folder):
            full_path = os.path.join(self.saves_folder, fname)
            if not os.path.isfile(full_path):
                continue

            m = pattern.match(fname)
            if not m:
                continue

            slot_hex = m.group(1).upper()
            ver_num = int(m.group(2)) if m.group(2) is not None else None

            try:
                sz = os.path.getsize(full_path)
                mtime = os.path.getmtime(full_path)
            except Exception:
                continue

            if slot_hex not in self.slots:
                try:
                    slot_dec = int(slot_hex, 16)
                except ValueError:
                    slot_dec = 0
                self.slots[slot_hex] = SaveSlotInfo(slot_hex, slot_dec, is_autosave=(slot_dec == 1))

            s_info = self.slots[slot_hex]
            s_info.total_size += sz

            if ver_num is None:
                s_info.main_file = full_path
                s_info.main_size = sz
                s_info.main_mtime = mtime
                # Check for 0-byte or corrupted header
                if sz == 0:
                    s_info.is_corrupted = True
                    s_info.corruption_reason = "Main save file is 0-byte (empty)."
                elif sz < 96:
                    s_info.is_corrupted = True
                    s_info.corruption_reason = "Main save file is smaller than 96 bytes."
            else:
                s_info.versions.append({
                    "ver": ver_num,
                    "path": full_path,
                    "filename": fname,
                    "size": sz,
                    "mtime": mtime
                })

        # Sort versions by version number (ver0 is most recent EA backup)
        for s_info in self.slots.values():
            s_info.versions.sort(key=lambda x: x["ver"])
            if not s_info.main_file and s_info.versions:
                s_info.is_corrupted = True
                s_info.corruption_reason = "Main save file missing, only backup .ver files exist."
                s_info.main_mtime = s_info.versions[0]["mtime"]

        return self.slots

    def create_snapshot(self, label: str, slot_hex: Optional[str] = None, notes: str = "") -> Tuple[bool, str]:
        """
        Creates a point-in-time snapshot with metadata manifest.
        If slot_hex is specified, archives only that slot; otherwise archives all slots.
        """
        if not os.path.isdir(self.saves_folder):
            return False, "Saves folder not found."

        os.makedirs(self.archive_folder, exist_ok=True)
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        slug = re.sub(r"[^a-zA-Z0-9_-]", "_", label.strip())[:25] or "snapshot"
        snapshot_id = f"snap_{stamp}_{slug}"
        snap_dir = os.path.join(self.archive_folder, snapshot_id)
        os.makedirs(snap_dir, exist_ok=True)

        copied_files = []
        pattern = (
            re.compile(rf"^slot_{slot_hex}\.save(?:\.ver\d+)?$", re.IGNORECASE)
            if slot_hex
            else re.compile(r"^slot_[0-9a-fA-F]+\.save(?:\.ver\d+)?$", re.IGNORECASE)
        )

        for fname in os.listdir(self.saves_folder):
            if pattern.match(fname):
                src = os.path.join(self.saves_folder, fname)
                dst = os.path.join(snap_dir, fname)
                try:
                    shutil.copy2(src, dst)
                    copied_files.append(fname)
                except Exception:
                    pass

        manifest = {
            "snapshot_id": snapshot_id,
            "label": label,
            "notes": notes,
            "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "slot_hex": slot_hex or "ALL",
            "file_count": len(copied_files),
            "files": copied_files
        }

        with open(os.path.join(snap_dir, "manifest.json"), "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return True, snapshot_id

    def rollback_slot_to_version(self, slot_hex: str, target_ver: int = 0) -> Tuple[bool, str]:
        """
        Rolls back a save slot to .ver0 (or specific target_ver).
        Automatically creates a safety backup checkpoint of the current state first!
        """
        self.scan_slots()
        slot_hex = slot_hex.upper()
        if slot_hex not in self.slots:
            return False, f"Slot {slot_hex} not found."

        slot = self.slots[slot_hex]
        backup_ver_info = next((v for v in slot.versions if v["ver"] == target_ver), None)
        if not backup_ver_info:
            return False, f"Version .ver{target_ver} does not exist for Slot {slot_hex}."

        # Safety checkpoint before rollback
        self.create_snapshot(f"Safety_PreRollback_{slot_hex}", slot_hex=slot_hex, notes="Auto-checkpoint before rollback")

        target_backup_path = backup_ver_info["path"]
        main_save_path = os.path.join(self.saves_folder, f"Slot_{slot_hex}.save")

        try:
            shutil.copy2(target_backup_path, main_save_path)
            self.scan_slots()
            return True, f"Slot {slot_hex} successfully rolled back to .ver{target_ver}."
        except Exception as e:
            return False, f"Failed to perform rollback: {e}"

    def list_snapshots(self) -> List[Dict[str, any]]:
        """Lists all existing point-in-time snapshots in the archive folder."""
        snapshots = []
        if not os.path.isdir(self.archive_folder):
            return snapshots

        for d in os.listdir(self.archive_folder):
            d_path = os.path.join(self.archive_folder, d)
            if os.path.isdir(d_path):
                manifest_file = os.path.join(d_path, "manifest.json")
                if os.path.isfile(manifest_file):
                    try:
                        with open(manifest_file, "r", encoding="utf-8") as f:
                            data = json.load(f)
                            data["folder_path"] = d_path
                            snapshots.append(data)
                    except Exception:
                        pass

        snapshots.sort(key=lambda x: x.get("created_at", ""), reverse=True)
        return snapshots

    def restore_snapshot(self, snapshot_id: str) -> Tuple[bool, str]:
        """Restores save files from a snapshot directory back into saves/."""
        snap_dir = os.path.join(self.archive_folder, snapshot_id)
        manifest_file = os.path.join(snap_dir, "manifest.json")
        if not os.path.isfile(manifest_file):
            return False, "Snapshot manifest not found."

        try:
            with open(manifest_file, "r", encoding="utf-8") as f:
                manifest = json.load(f)
        except Exception as e:
            return False, f"Corrupted snapshot manifest: {e}"

        # Pre-restore safety snapshot
        self.create_snapshot("Safety_PreRestore", notes=f"Auto-checkpoint before restoring {snapshot_id}")

        restored_count = 0
        for fname in manifest.get("files", []):
            src = os.path.join(snap_dir, fname)
            dst = os.path.join(self.saves_folder, fname)
            if os.path.isfile(src):
                try:
                    shutil.copy2(src, dst)
                    restored_count += 1
                except Exception:
                    pass

        self.scan_slots()
        return True, f"Successfully restored {restored_count} save files from snapshot '{manifest.get('label')}'."

    def purge_old_versions(self, keep_latest_ver: bool = True) -> Tuple[int, int]:
        """
        Deletes old rolling backup files (.ver1 - .ver4), optionally keeping .ver0.
        Returns: (deleted_file_count, bytes_freed)
        """
        self.scan_slots()
        deleted = 0
        bytes_freed = 0

        for slot in self.slots.values():
            for v in slot.versions:
                if keep_latest_ver and v["ver"] == 0:
                    continue  # Keep .ver0 as standard EA emergency backup
                try:
                    sz = v["size"]
                    os.remove(v["path"])
                    deleted += 1
                    bytes_freed += sz
                except Exception:
                    pass

        self.scan_slots()
        return deleted, bytes_freed
