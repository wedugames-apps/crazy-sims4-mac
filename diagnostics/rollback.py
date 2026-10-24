"""
==============================================================================
Crazy The Sims 4 Project - Save Game Rollback & Recovery Diagnostic
==============================================================================
Specialized 1-Click recovery engine for corrupted, missing, or broken save slots.
Leverages the rolling backup system (.ver0 - .ver4) and snapshot checkpoints.
"""

import os
import shutil
from typing import Dict, List, Optional, Tuple
from core.archivist import SaveArchivist, SaveSlotInfo


class SaveRecoveryDiagnostic:
    """Diagnoses save corruption and manages 1-Click automated recovery."""

    def __init__(self, saves_folder: str):
        self.saves_folder: str = os.path.abspath(saves_folder)
        self.archivist: SaveArchivist = SaveArchivist(self.saves_folder)

    def diagnose_all_slots(self) -> Dict[str, any]:
        """
        Inspects all save slots for:
        - 0-byte corrupted save files
        - Truncated save files (< 96 bytes)
        - Missing main save files with orphaned .ver0 backups
        - Available recovery targets for each slot
        """
        slots = self.archivist.scan_slots()
        corrupted_slots = []
        healthy_slots = []

        for s in slots.values():
            if s.is_corrupted:
                corrupted_slots.append(s)
            else:
                healthy_slots.append(s)

        return {
            "total_slots": len(slots),
            "corrupted_count": len(corrupted_slots),
            "healthy_count": len(healthy_slots),
            "corrupted_slots": corrupted_slots,
            "healthy_slots": healthy_slots,
            "all_slots": list(slots.values())
        }

    def auto_recover_slot(self, slot_hex: str) -> Tuple[bool, str]:
        """
        Recovers a corrupted or damaged save slot using its newest backup version (.ver0).
        Automatically creates a safety checkpoint of current files first.
        """
        slot_hex = slot_hex.upper()
        slots = self.archivist.scan_slots()
        if slot_hex not in slots:
            return False, f"Save slot {slot_hex} does not exist."

        slot = slots[slot_hex]
        if not slot.versions:
            return False, f"No backup versions (.ver0 - .ver4) found for Slot {slot_hex}."

        target_ver = slot.versions[0]["ver"]
        success, msg = self.archivist.rollback_slot_to_version(slot_hex, target_ver=target_ver)
        return success, msg

    def rollback_slot(self, slot_id: any, target_ver: int = 0) -> Tuple[bool, str]:
        """
        Rollback slot alias supporting hex strings, numbers, or slot names.
        """
        slot_str = str(slot_id).upper().replace("SLOT_", "").replace(".SAVE", "").strip()
        if target_ver == 0:
            return self.auto_recover_slot(slot_str)
        return self.archivist.rollback_slot_to_version(slot_str, target_ver=target_ver)

    def auto_recover_all_corrupted(self) -> Tuple[int, List[str]]:
        """
        Finds all corrupted save slots and automatically attempts recovery from .ver0.
        Returns: (recovered_count, log_messages)
        """
        diag = self.diagnose_all_slots()
        recovered = 0
        logs = []

        for slot in diag["corrupted_slots"]:
            if slot.versions:
                ok, msg = self.auto_recover_slot(slot.slot_hex)
                if ok:
                    recovered += 1
                    logs.append(f"Recovered Slot {slot.slot_hex} from .ver{slot.versions[0]['ver']}")
                else:
                    logs.append(f"Failed to recover Slot {slot.slot_hex}: {msg}")
            else:
                logs.append(f"Slot {slot.slot_hex} is corrupted and has no backup versions.")

        return recovered, logs
