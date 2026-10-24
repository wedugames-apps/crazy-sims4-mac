"""
==============================================================================
Crazy Doctor for The Sims 4 (macOS Edition) - iCloud Drive & Folder Merger
==============================================================================
Detects and repairs:
- iCloud Drive evicted / dateless "ghost" files in Mods/ and saves/ (.icloud placeholders)
- Split Documents folders (Local ~/Documents vs iCloud Drive ~/Library/Mobile Documents)
"""

import os
from typing import Dict, List, Optional, Tuple
from core.system import SystemIntegration


class CloudFolderManager:
    """Detects and resolves macOS iCloud Drive eviction anomalies and split Documents."""

    def __init__(self, primary_user_folder: str):
        self.primary_user_folder: str = os.path.abspath(primary_user_folder)
        self.mods_folder: str = os.path.join(self.primary_user_folder, "Mods")
        self.saves_folder: str = os.path.join(self.primary_user_folder, "saves")

    def inspect_ghost_files(self) -> Dict[str, any]:
        """Scans Mods and saves folders for unhydrated iCloud ghost files (.icloud / dateless)."""
        mods_ghosts = SystemIntegration.scan_for_ghost_files(self.mods_folder)
        saves_ghosts = SystemIntegration.scan_for_ghost_files(self.saves_folder)

        all_ghosts = mods_ghosts + saves_ghosts
        return {
            "total_ghosts": len(all_ghosts),
            "mods_ghosts": mods_ghosts,
            "saves_ghosts": saves_ghosts,
            "has_ghost_files": len(all_ghosts) > 0,
            "ghost_files": all_ghosts
        }

    def hydrate_all_ghosts(self) -> Tuple[int, int]:
        """
        Forces all detected iCloud ghost files to be downloaded/hydrated locally.
        Returns: (success_count, fail_count)
        """
        inspection = self.inspect_ghost_files()
        ghosts = inspection["ghost_files"]
        success = 0
        failed = 0

        for f in ghosts:
            if SystemIntegration.hydrate_file(f):
                success += 1
            else:
                failed += 1

        return success, failed

    def inspect_split_documents(self) -> Optional[Dict[str, any]]:
        """Checks if user has split Electronic Arts folders across Local and iCloud Documents."""
        return SystemIntegration.detect_split_documents()

    def merge_split_into_primary(self, secondary_folder: str) -> Tuple[int, str]:
        """Merges a secondary Sims 4 folder into the active primary user folder."""
        if not secondary_folder or not os.path.isdir(secondary_folder):
            return 0, "Secondary folder not found."
        if os.path.normcase(os.path.abspath(secondary_folder)) == os.path.normcase(self.primary_user_folder):
            return 0, "Source and destination folders are identical."

        return SystemIntegration.merge_split_folders(secondary_folder, self.primary_user_folder)
