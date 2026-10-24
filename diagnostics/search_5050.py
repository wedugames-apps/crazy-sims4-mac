"""
==============================================================================
Crazy The Sims 4 Project - 50/50 Binary Search Automator
==============================================================================
Automates the classic Sims 4 50/50 troubleshooting technique to pinpoint the
exact offending mod causing crashes or UI glitches in log2(N) steps.
"""

import os
import json
import shutil
from typing import Dict, List, Optional, Tuple


class Method5050Automator:
    """State machine and file manager for 50/50 mod troubleshooting."""

    STATE_FILE = "5050_state.json"

    def __init__(self, mods_folder: str, staging_folder: Optional[str] = None):
        self.mods_folder: str = os.path.abspath(mods_folder)
        self.staging_folder: str = (
            os.path.abspath(staging_folder)
            if staging_folder
            else os.path.join(os.path.dirname(self.mods_folder), "Mods_5050_Staging")
        )
        self.state_file_path: str = os.path.join(self.staging_folder, self.STATE_FILE)

        self.current_step: int = 0
        self.suspect_pool: List[str] = []
        self.active_batch: List[str] = []
        self.disabled_batch: List[str] = []
        self.eliminated_safe: List[str] = []
        self.is_active: bool = False
        self.identified_culprit: Optional[str] = None

        self.load_state()

    def start_session(self) -> Tuple[bool, str]:
        """Initializes a new 50/50 troubleshooting session."""
        if not os.path.isdir(self.mods_folder):
            return False, "Mods folder does not exist."

        os.makedirs(self.staging_folder, exist_ok=True)

        # Collect all active mod files
        mod_files = []
        for root, _, files in os.walk(self.mods_folder):
            for f in files:
                if f.lower().endswith((".package", ".ts4script")):
                    mod_files.append(os.path.relpath(os.path.join(root, f), self.mods_folder))

        if len(mod_files) < 2:
            return False, f"Not enough mod files ({len(mod_files)}) to run a 50/50 search."

        self.suspect_pool = sorted(mod_files)
        self.eliminated_safe = []
        self.current_step = 0
        self.is_active = True
        self.identified_culprit = None

        self._prepare_next_split()
        self.save_state()

        return True, f"50/50 session started with {len(self.suspect_pool)} suspect mods."

    def _prepare_next_split(self):
        """Divides suspect pool in half, staging half and keeping half active."""
        if len(self.suspect_pool) == 1:
            self.identified_culprit = self.suspect_pool[0]
            self.is_active = False
            self.restore_safe_mods()
            self.save_state()
            return

        mid = len(self.suspect_pool) // 2
        self.active_batch = self.suspect_pool[:mid]
        self.disabled_batch = self.suspect_pool[mid:]
        self.current_step += 1

        # 1. Any mod not in active_batch (disabled_batch + eliminated_safe) must be staged
        for rel in list(self.disabled_batch) + list(self.eliminated_safe):
            src = os.path.join(self.mods_folder, rel)
            dst = os.path.join(self.staging_folder, rel)
            if os.path.isfile(src):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                try:
                    shutil.move(src, dst)
                except Exception:
                    pass

        # 2. Ensure active_batch is in mods_folder
        for rel in self.active_batch:
            src = os.path.join(self.staging_folder, rel)
            dst = os.path.join(self.mods_folder, rel)
            if os.path.isfile(src):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                try:
                    shutil.move(src, dst)
                except Exception:
                    pass

    def record_test_result(self, is_glitch_still_present: bool) -> Tuple[bool, str]:
        """
        Records the user's game test result:
        - True: Glitch still occurred -> Culprit is inside current active batch!
        - False: Glitch is gone -> Current active batch is innocent! Culprit is in staged batch!
        """
        if not self.is_active:
            return False, "No active 50/50 session running."

        if is_glitch_still_present:
            # Active batch contains the culprit! Disabled batch is proven innocent.
            self.eliminated_safe.extend(self.disabled_batch)
            self.suspect_pool = list(self.active_batch)
        else:
            # Active batch is safe! Culprit is in the disabled batch.
            self.eliminated_safe.extend(self.active_batch)
            self.suspect_pool = list(self.disabled_batch)

        if len(self.suspect_pool) == 1:
            self.identified_culprit = self.suspect_pool[0]
            self.is_active = False
            # Ensure culprit is present in mods_folder
            culprit_staged = os.path.join(self.staging_folder, self.identified_culprit)
            culprit_mods = os.path.join(self.mods_folder, self.identified_culprit)
            if os.path.isfile(culprit_staged):
                os.makedirs(os.path.dirname(culprit_mods), exist_ok=True)
                try:
                    shutil.move(culprit_staged, culprit_mods)
                except Exception:
                    pass
            # Restore all proven safe mods back to Mods/
            self.restore_safe_mods()
            self.save_state()
            return True, f"Offending mod successfully identified: {self.identified_culprit}"

        self._prepare_next_split()
        self.save_state()
        return True, f"Step {self.current_step}: Narrowed down to {len(self.suspect_pool)} mods."

    def restore_safe_mods(self) -> int:
        """Restores all innocent/eliminated safe mods from staging back to Mods folder."""
        restored = 0
        for rel in self.eliminated_safe:
            src = os.path.join(self.staging_folder, rel)
            dst = os.path.join(self.mods_folder, rel)
            if os.path.isfile(src):
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                try:
                    shutil.move(src, dst)
                    restored += 1
                except Exception:
                    pass
        return restored

    def isolate_culprit(self) -> Tuple[bool, str]:
        """Disables the identified culprit mod with a .disabled suffix."""
        if not self.identified_culprit:
            return False, "No culprit has been identified yet."
        p = os.path.join(self.mods_folder, self.identified_culprit)
        if os.path.isfile(p):
            try:
                os.rename(p, p + ".disabled")
                return True, f"Culprit disabled: {os.path.basename(p)}.disabled"
            except Exception as e:
                return False, str(e)
        return False, f"Culprit file {self.identified_culprit} not found in Mods folder."

    def cancel_and_restore(self) -> Tuple[bool, str]:
        """Cancels session and restores all mods from staging back to Mods/."""
        if not os.path.isdir(self.staging_folder):
            return True, "No staged files to restore."

        restored = 0
        for root, _, files in os.walk(self.staging_folder):
            for f in files:
                if f == self.STATE_FILE:
                    continue
                src = os.path.join(root, f)
                rel = os.path.relpath(src, self.staging_folder)
                dst = os.path.join(self.mods_folder, rel)
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                try:
                    shutil.move(src, dst)
                    restored += 1
                except Exception:
                    pass

        # Cleanup state file
        if os.path.isfile(self.state_file_path):
            try:
                os.remove(self.state_file_path)
            except Exception:
                pass

        # Cleanup empty directories in staging
        for root, dirs, _ in os.walk(self.staging_folder, topdown=False):
            for d in dirs:
                try:
                    os.rmdir(os.path.join(root, d))
                except Exception:
                    pass

        self.is_active = False
        self.current_step = 0
        self.suspect_pool = []
        return True, f"Session cancelled. Restored {restored} mod files to Mods folder."

    def save_state(self):
        """Saves session state to JSON."""
        state = {
            "current_step": self.current_step,
            "suspect_pool": self.suspect_pool,
            "active_batch": self.active_batch,
            "disabled_batch": self.disabled_batch,
            "eliminated_safe": self.eliminated_safe,
            "is_active": self.is_active,
            "identified_culprit": self.identified_culprit
        }
        try:
            with open(self.state_file_path, "w", encoding="utf-8") as f:
                json.dump(state, f, indent=2)
        except Exception:
            pass

    def load_state(self):
        """Loads existing session state from JSON if available."""
        if os.path.isfile(self.state_file_path):
            try:
                with open(self.state_file_path, "r", encoding="utf-8") as f:
                    state = json.load(f)
                self.current_step = state.get("current_step", 0)
                self.suspect_pool = state.get("suspect_pool", [])
                self.active_batch = state.get("active_batch", [])
                self.disabled_batch = state.get("disabled_batch", [])
                self.eliminated_safe = state.get("eliminated_safe", [])
                self.is_active = state.get("is_active", False)
                self.identified_culprit = state.get("identified_culprit")
            except Exception:
                pass


FiftyFiftyTroubleshooter = Method5050Automator
