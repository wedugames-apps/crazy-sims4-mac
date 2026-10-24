"""
==============================================================================
Crazy Doctor for The Sims 4 (macOS Edition) - System Integration Engine
==============================================================================
Native macOS environment manager:
- macOS User Folders resolution (~/Documents/Electronic Arts/The Sims 4/ and iCloud Drive)
- macOS Application Bundle resolution (/Applications/The Sims 4.app)
- iCloud Drive eviction & dateless ghost file detection (.icloud and APFS purge blocks)
- Split Documents detection & safe bidirectional merge
- macOS Full Disk Access & file permission verification
- System architecture detection (Apple Silicon M1/M2/M3/M4 arm64 & Intel x86_64)
"""

import os
import sys
import shutil
import platform
import subprocess
from typing import Dict, List, Optional, Set, Tuple


class SystemIntegration:
    """Native macOS system and file environment manager for The Sims 4."""

    @staticmethod
    def is_macos() -> bool:
        """Returns True if currently executing on macOS (Darwin)."""
        return sys.platform == "darwin"

    @staticmethod
    def get_system_architecture() -> str:
        """
        Returns the host system architecture.
        e.g., 'arm64' (Apple Silicon M1/M2/M3/M4) or 'x86_64' (Intel Mac).
        """
        arch = platform.machine().lower()
        if arch in ("arm64", "aarch64"):
            return "arm64 (Apple Silicon)"
        elif arch in ("x86_64", "amd64"):
            return "x86_64 (Intel)"
        return arch

    @staticmethod
    def get_user_documents_folders() -> List[str]:
        """
        Discovers all possible Documents folders across native macOS:
        1. Standard user Documents (~/Documents)
        2. iCloud Drive synced Documents (~/Library/Mobile Documents/com~apple~CloudDocs/Documents)
        3. Environment variable overrides (SIMS4_DOCUMENTS_DIR, etc.)
        """
        candidates: List[str] = []
        home = os.path.expanduser("~")

        # 1. Environment variable override
        for env_var in ("SIMS4_DOCUMENTS_DIR", "SIMS4_DOCS", "ELECTRONIC_ARTS_DIR"):
            env_val = os.environ.get(env_var)
            if env_val:
                expanded = os.path.expanduser(os.path.expandvars(env_val))
                if os.path.isdir(expanded) and expanded not in candidates:
                    candidates.append(expanded)

        # 2. Standard macOS User Documents
        local_docs = os.path.join(home, "Documents")
        if os.path.isdir(local_docs) and local_docs not in candidates:
            candidates.append(local_docs)

        # 3. macOS iCloud Drive Synced Documents
        icloud_docs = os.path.join(
            home, "Library", "Mobile Documents", "com~apple~CloudDocs", "Documents"
        )
        if os.path.isdir(icloud_docs) and icloud_docs not in candidates:
            candidates.append(icloud_docs)

        # 4. Fallback for testing / simulated environments (e.g. non-macOS test runner)
        if not candidates:
            candidates.append(local_docs)

        return candidates

    @classmethod
    def find_sims4_user_folder(cls) -> Optional[str]:
        """
        Detects the active Electronic Arts/The Sims 4 folder on macOS.
        Prioritizes the active folder based on Options.ini presence, latest mtime,
        and content in Mods and saves.
        """
        doc_dirs = cls.get_user_documents_folders()
        valid_folders: List[str] = []

        for d in doc_dirs:
            ts4_path = os.path.join(d, "Electronic Arts", "The Sims 4")
            if os.path.isdir(ts4_path) and ts4_path not in valid_folders:
                valid_folders.append(ts4_path)

        if not valid_folders:
            # Check default path even if not yet created
            default_path = os.path.expanduser("~/Documents/Electronic Arts/The Sims 4")
            if os.path.isdir(default_path):
                return default_path
            return None

        def _score_folder(p: str) -> float:
            score = 0.0
            ini_file = os.path.join(p, "Options.ini")
            if os.path.isfile(ini_file):
                score += 1_000_000_000.0
                try:
                    score += os.path.getmtime(ini_file)
                except Exception:
                    pass
            mods_dir = os.path.join(p, "Mods")
            if os.path.isdir(mods_dir):
                score += 100_000.0
                try:
                    score += len(os.listdir(mods_dir)) * 10.0
                except Exception:
                    pass
            saves_dir = os.path.join(p, "saves")
            if os.path.isdir(saves_dir):
                score += 50_000.0
            return score

        valid_folders.sort(key=_score_folder, reverse=True)
        return valid_folders[0]

    @staticmethod
    def find_sims4_game_binary() -> Optional[str]:
        """
        Locates the Sims 4 executable or application bundle on macOS.
        Resolves to The Sims 4.app bundle or inner executable.
        """
        candidates = [
            "/Applications/The Sims 4.app",
            os.path.expanduser("~/Applications/The Sims 4.app"),
            "/Applications/EA Games/The Sims 4.app",
            os.path.expanduser("~/Library/Application Support/Steam/steamapps/common/The Sims 4/The Sims 4.app"),
        ]

        # Check bundle paths
        for app_path in candidates:
            if os.path.isdir(app_path):
                # Inner Unix executable
                inner_exec = os.path.join(app_path, "Contents", "MacOS", "The Sims 4")
                if sys.platform == "darwin" or app_path.startswith("/"):
                    inner_exec = inner_exec.replace("\\", "/")
                if os.path.isfile(inner_exec):
                    return inner_exec
                return app_path

        # If on Windows/Linux during test simulations, check fallback
        if sys.platform == "win32":
            drives = ["C:", "D:"]
            for drv in drives:
                p = os.path.join(drv, os.sep, r"Program Files\EA Games\The Sims 4\Game\Bin\TS4_x64.exe")
                if os.path.isfile(p):
                    return p

        return None

    # ------------------------------------------------------------------------
    # ICLOUD DRIVE EVICTION & DATELESS GHOST FILE DETECTION
    # ------------------------------------------------------------------------
    @classmethod
    def is_ghost_cloud_file(cls, file_path: str) -> bool:
        """
        Detects if a file is an evicted / unhydrated iCloud Drive ghost file.
        In macOS iCloud Drive ('Optimize Mac Storage'):
        1. Evicted files are renamed with a leading dot and '.icloud' extension (e.g. '.MyMod.package.icloud')
        2. Files ending with '.icloud'
        3. Dataless APFS files where file size is reported (>0) but allocated disk blocks == 0
        4. 0-byte packages or saves where header is missing
        """
        base_name = os.path.basename(file_path)

        # 1. Direct iCloud placeholder extension
        if base_name.endswith(".icloud"):
            return True

        if not os.path.isfile(file_path):
            return False

        try:
            stat_res = os.stat(file_path)
            # 2. Dataless APFS file check (st_blocks == 0 while st_size > 0)
            if hasattr(stat_res, "st_blocks"):
                if stat_res.st_size > 0 and stat_res.st_blocks == 0:
                    return True

            # 3. Zero-byte mod package or save file (indicates evicted placeholder)
            if stat_res.st_size == 0 and (
                base_name.lower().endswith(".package") or
                base_name.lower().endswith(".ts4script") or
                base_name.lower().endswith(".save")
            ):
                return True

            # 4. macOS Extended Attributes (xattr) check for iCloud eviction
            if sys.platform == "darwin":
                try:
                    import xattr
                    attrs = xattr.listxattr(file_path)
                    if any("clouddocs" in a.lower() or "dataless" in a.lower() for a in attrs):
                        return True
                except Exception:
                    pass

        except Exception:
            pass

        return False

    @classmethod
    def scan_for_ghost_files(cls, target_dir: str) -> List[str]:
        """
        Scans a directory (e.g., Mods or saves) for all evicted/ghost cloud files.
        """
        ghosts: List[str] = []
        if not target_dir or not os.path.isdir(target_dir):
            return ghosts

        for root, _, files in os.walk(target_dir):
            for f in files:
                full_path = os.path.join(root, f)
                if cls.is_ghost_cloud_file(full_path):
                    ghosts.append(full_path)

        return ghosts

    @classmethod
    def hydrate_file(cls, file_path: str) -> bool:
        """
        Forces macOS or cloud engine to hydrate an evicted file.
        If file has .icloud extension, attempts 'brctl download' on macOS.
        Otherwise reads file bytes in chunks to trigger kernel hydration.
        """
        if not file_path or not os.path.exists(file_path):
            return False

        # If on macOS and file is .icloud, trigger brctl
        if sys.platform == "darwin":
            try:
                subprocess.run(
                    ["brctl", "download", file_path],
                    capture_output=True,
                    timeout=5
                )
            except Exception:
                pass

        # Trigger hydration by reading stream
        try:
            with open(file_path, "rb") as f:
                while True:
                    chunk = f.read(65536)
                    if not chunk:
                        break
            return True
        except Exception:
            return False

    @classmethod
    def hydrate_all_ghost_files(cls, target_dir: str) -> Tuple[int, int]:
        """
        Finds and hydrates all ghost files under target_dir.
        Returns: (hydrated_count, failed_count)
        """
        ghosts = cls.scan_for_ghost_files(target_dir)
        hydrated = 0
        failed = 0

        for g in ghosts:
            if cls.hydrate_file(g):
                hydrated += 1
            else:
                failed += 1

        return hydrated, failed

    # ------------------------------------------------------------------------
    # SPLIT DOCUMENTS DETECTION & SAFE MERGING
    # ------------------------------------------------------------------------
    @classmethod
    def detect_split_documents(cls) -> Optional[Dict[str, any]]:
        """
        Detects whether user has split Electronic Arts folders
        (e.g., one in Local ~/Documents and another in iCloud ~/Library/Mobile Documents).
        """
        doc_dirs = cls.get_user_documents_folders()
        ea_folders = []
        for d in doc_dirs:
            p = os.path.join(d, "Electronic Arts", "The Sims 4")
            if os.path.isdir(p) and p not in ea_folders:
                ea_folders.append(p)

        if len(ea_folders) <= 1:
            return None

        details = []
        for p in ea_folders:
            mods_p = os.path.join(p, "Mods")
            saves_p = os.path.join(p, "saves")
            m_count = len(os.listdir(mods_p)) if os.path.isdir(mods_p) else 0
            s_count = len(os.listdir(saves_p)) if os.path.isdir(saves_p) else 0
            details.append({
                "path": p,
                "mods_count": m_count,
                "saves_count": s_count,
                "has_options_ini": os.path.isfile(os.path.join(p, "Options.ini"))
            })

        return {
            "folder_count": len(ea_folders),
            "folders": ea_folders,
            "details": details
        }

    @classmethod
    def merge_split_folders(cls, source_folder: str, target_folder: str) -> Tuple[int, str]:
        """
        Safely merges files from a secondary/dormant Sims 4 folder into the primary one.
        Never overwrites newer destination files.
        """
        if not os.path.isdir(source_folder) or not os.path.isdir(target_folder):
            return 0, "Invalid source or target folder."

        copied = 0
        for root, _, files in os.walk(source_folder):
            rel_dir = os.path.relpath(root, source_folder)
            dest_dir = os.path.join(target_folder, rel_dir)
            os.makedirs(dest_dir, exist_ok=True)

            for f in files:
                src_file = os.path.join(root, f)
                dst_file = os.path.join(dest_dir, f)

                if os.path.exists(dst_file):
                    try:
                        if os.path.getmtime(dst_file) >= os.path.getmtime(src_file):
                            continue
                    except Exception:
                        continue

                try:
                    shutil.copy2(src_file, dst_file)
                    copied += 1
                except Exception:
                    pass

        return copied, f"Successfully merged {copied} files into primary folder."

    # ------------------------------------------------------------------------
    # MACOS PERMISSION & SECURITY CHECKS
    # ------------------------------------------------------------------------
    @classmethod
    def check_permissions(cls, target_folder: Optional[str] = None) -> Dict[str, any]:
        """
        Verifies macOS file write permissions and Full Disk Access status.
        Sims 4 requires write permissions to Documents/Electronic Arts/The Sims 4.
        """
        folder = target_folder or cls.find_sims4_user_folder() or os.path.expanduser("~/Documents")
        result = {
            "folder": folder,
            "exists": os.path.isdir(folder),
            "readable": os.access(folder, os.R_OK) if os.path.exists(folder) else False,
            "writable": os.access(folder, os.W_OK) if os.path.exists(folder) else False,
            "full_disk_access_ok": True,
            "warning": None
        }

        if not result["writable"]:
            result["full_disk_access_ok"] = False
            result["warning"] = (
                "Write access is restricted. On macOS, grant 'Full Disk Access' "
                "or 'Files and Folders' permissions in System Settings > Privacy & Security."
            )

        return result
