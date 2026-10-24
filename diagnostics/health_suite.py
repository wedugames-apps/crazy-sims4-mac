"""
==============================================================================
Crazy Doctor for The Sims 4 (macOS Edition) - Master Health Suite & Auto-Fixer
==============================================================================
Orchestrates all diagnostics into a unified 1-Click Full Scan for macOS, produces
an aggregate Health Score (0-100) with status classification (Critical Red,
Warning Yellow, Healthy Green), and executes safe 1-Click Auto-Fix All operations
with automated quarantine backups.
"""

import os
import re
import glob
import shutil
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Tuple

from core.system import SystemIntegration
from core.dbpf import DBPFPackage
from diagnostics.graphics import GraphicsDiagnostic
from diagnostics.cloud_merge import CloudFolderManager
from diagnostics.mesh_hunter import MeshHunter
from diagnostics.script_doctor import ScriptModFlattener, CrashDecoder
from diagnostics.rollback import SaveRecoveryDiagnostic
from diagnostics.ea_killer import ProcessKiller
from diagnostics.townie_sanitizer import TownieSanitizer


class HealthIssue:
    """Represents a diagnostic issue identified during scan."""

    def __init__(
        self,
        category: str,
        title: str,
        description: str,
        severity: str = "WARNING",  # CRITICAL, WARNING, INFO
        affected_files: Optional[List[str]] = None,
        auto_fixable: bool = False
    ):
        self.category: str = category
        self.title: str = title
        self.description: str = description
        self.severity: str = severity.upper()
        self.affected_files: List[str] = affected_files or []
        self.auto_fixable: bool = auto_fixable

    def __repr__(self) -> str:
        return f"<HealthIssue [{self.severity}] {self.title}>"


class MasterHealthSuite:
    """Comprehensive diagnostic orchestrator for The Sims 4 on macOS."""

    def __init__(self, ts4_user_folder: Optional[str] = None):
        self.ts4_user_folder: str = (
            os.path.abspath(ts4_user_folder)
            if ts4_user_folder
            else (SystemIntegration.find_sims4_user_folder() or "")
        )
        self.mods_folder: str = os.path.join(self.ts4_user_folder, "Mods") if self.ts4_user_folder else ""
        self.saves_folder: str = os.path.join(self.ts4_user_folder, "saves") if self.ts4_user_folder else ""
        self.quarantine_folder: str = (
            os.path.join(self.ts4_user_folder, "Quarantine_WeduGames")
            if self.ts4_user_folder
            else ""
        )

        # Diagnostics Engines
        self.graphics_diag: Optional[GraphicsDiagnostic] = (
            GraphicsDiagnostic(self.ts4_user_folder) if self.ts4_user_folder else None
        )
        self.cloud_mgr: Optional[CloudFolderManager] = (
            CloudFolderManager(self.ts4_user_folder) if self.ts4_user_folder else None
        )
        self.mesh_hunter: Optional[MeshHunter] = (
            MeshHunter(self.mods_folder) if self.mods_folder else None
        )
        self.script_flattener: Optional[ScriptModFlattener] = (
            ScriptModFlattener(self.mods_folder) if self.mods_folder else None
        )
        self.crash_decoder: Optional[CrashDecoder] = (
            CrashDecoder(self.ts4_user_folder) if self.ts4_user_folder else None
        )
        self.save_recovery: Optional[SaveRecoveryDiagnostic] = (
            SaveRecoveryDiagnostic(self.saves_folder) if self.saves_folder else None
        )
        self.townie_sanitizer: Optional[TownieSanitizer] = (
            TownieSanitizer(self.mods_folder) if self.mods_folder else None
        )

        self.issues: List[HealthIssue] = []
        self.health_score: int = 100
        self.health_status: str = "Healthy Green"
        self.last_scan_time: Optional[str] = None

    def run_full_scan(self, deep_mesh_scan: bool = True) -> Dict[str, any]:
        """Runs an end-to-end multi-point health scan for macOS."""
        self.issues.clear()
        self.health_score = 100

        if not self.ts4_user_folder or not os.path.isdir(self.ts4_user_folder):
            self.issues.append(HealthIssue(
                category="System",
                title="The Sims 4 Folder Not Found",
                description="Could not locate Electronic Arts/The Sims 4 in Documents or iCloud Drive.",
                severity="CRITICAL",
                auto_fixable=False
            ))
            self.health_score = 0
            self.health_status = "Critical Red"
            return self.get_summary()

        # 1. Options.ini Check (Script mods enabled, mods enabled)
        ini_path = os.path.join(self.ts4_user_folder, "Options.ini")
        if os.path.isfile(ini_path):
            try:
                with open(ini_path, "r", encoding="utf-8", errors="ignore") as f:
                    ini_text = f.read()

                m_dis = re.search(r"^\s*modsdisabled\s*=\s*(\d+)", ini_text, re.MULTILINE | re.IGNORECASE)
                if m_dis and int(m_dis.group(1)) == 1:
                    self.issues.append(HealthIssue(
                        category="Settings",
                        title="Custom Content Disabled in Game Options",
                        description="Game option 'modsdisabled' is 1. Mods & CC will not appear in-game.",
                        severity="CRITICAL",
                        affected_files=[ini_path],
                        auto_fixable=True
                    ))
                    self.health_score -= 25

                m_scr = re.search(r"^\s*scriptmodsenabled\s*=\s*(\d+)", ini_text, re.MULTILINE | re.IGNORECASE)
                if m_scr and int(m_scr.group(1)) == 0:
                    self.issues.append(HealthIssue(
                        category="Settings",
                        title="Script Mods Disabled in Game Options",
                        description="Game option 'scriptmodsenabled' is 0. All .ts4script gameplay mods are disabled.",
                        severity="CRITICAL",
                        affected_files=[ini_path],
                        auto_fixable=True
                    ))
                    self.health_score -= 25
            except Exception:
                pass

        # 2. Script Mod Depth Violations
        if self.script_flattener:
            violations = self.script_flattener.scan_depth_violations()
            if violations:
                aff = [v["current_path"] for v in violations]
                self.issues.append(HealthIssue(
                    category="Scripts",
                    title=f"{len(violations)} Script Mods Nested Too Deeply",
                    description=".ts4script files placed 2+ subfolders deep are ignored by the game engine.",
                    severity="CRITICAL",
                    affected_files=aff,
                    auto_fixable=True
                ))
                self.health_score -= min(20, len(violations) * 5)

        # 3. Crash & Exception Logs
        if self.crash_decoder:
            latest_crash = self.crash_decoder.get_latest_crash_report()
            if latest_crash and latest_crash["has_error"]:
                culprits = latest_crash["detected_culprits"]
                if culprits:
                    c = culprits[0]
                    self.issues.append(HealthIssue(
                        category="Crashes",
                        title=f"Crash Culprit: {c['mod_name']} ({c['author']})",
                        description=f"{c['advice']} (Found in {latest_crash['file']})",
                        severity="CRITICAL" if c["severity"] == "CRITICAL" else "WARNING",
                        affected_files=[latest_crash["path"]],
                        auto_fixable=False
                    ))
                    self.health_score -= 20
                elif latest_crash["raw_exception_type"]:
                    self.issues.append(HealthIssue(
                        category="Crashes",
                        title=f"Game Error: {latest_crash['raw_exception_type']}",
                        description=f"Unhandled exception recorded in {latest_crash['file']}.",
                        severity="WARNING",
                        affected_files=[latest_crash["path"]],
                        auto_fixable=False
                    ))
                    self.health_score -= 10

        # 4. Cache & Metal Shader Bloat
        if self.graphics_diag:
            cache_items = self.graphics_diag.inspect_cache_items()
            total_cache_bytes = sum(c["size"] for c in cache_items)
            if total_cache_bytes > 50 * 1024 * 1024:
                mb = total_cache_bytes / (1024 * 1024)
                self.issues.append(HealthIssue(
                    category="Cache",
                    title=f"Metal Shader & Thumbnail Cache Bloat ({mb:.1f} MB)",
                    description="Accumulated Metal shaders and localthumbcache cause stutter, visual glitches, and UI lag.",
                    severity="WARNING",
                    affected_files=[c["path"] for c in cache_items],
                    auto_fixable=True
                ))
                self.health_score -= 10

        # 5. iCloud Evicted / Ghost Files
        if self.cloud_mgr:
            ghost_info = self.cloud_mgr.inspect_ghost_files()
            if ghost_info["has_ghost_files"]:
                count = ghost_info["total_ghosts"]
                self.issues.append(HealthIssue(
                    category="Cloud",
                    title=f"{count} Evicted iCloud Ghost Files Detected",
                    description="Files offloaded by iCloud Drive (.icloud placeholders) freeze Sims 4 on load. Must be hydrated locally.",
                    severity="CRITICAL",
                    affected_files=ghost_info["ghost_files"],
                    auto_fixable=True
                ))
                self.health_score -= min(25, count * 5)

        # 6. Save Game Corruption
        if self.save_recovery:
            save_diag = self.save_recovery.diagnose_all_slots()
            if save_diag["corrupted_count"] > 0:
                aff_saves = [s.main_file for s in save_diag["corrupted_slots"] if s.main_file]
                self.issues.append(HealthIssue(
                    category="Saves",
                    title=f"{save_diag['corrupted_count']} Corrupted Save Slots Detected",
                    description="Corrupted or 0-byte save files found. Can be restored from rolling .ver0 backups.",
                    severity="CRITICAL",
                    affected_files=aff_saves,
                    auto_fixable=True
                ))
                self.health_score -= 25

        # 7. Zombie EA App / TS4 Processes
        zombies = ProcessKiller.list_running_targets()
        if zombies:
            names = [z["name"] for z in zombies]
            self.issues.append(HealthIssue(
                category="Processes",
                title=f"{len(zombies)} Hanging EA / TS4 Zombie Processes",
                description="Background services are locking files and may prevent mods or saves from saving.",
                severity="WARNING",
                affected_files=names,
                auto_fixable=True
            ))
            self.health_score -= 10

        # 8. macOS File Permissions (Full Disk Access)
        perm_info = SystemIntegration.check_permissions(self.ts4_user_folder)
        if not perm_info["writable"]:
            self.issues.append(HealthIssue(
                category="Security",
                title="macOS Write Access Restricted (Full Disk Access Required)",
                description=perm_info.get("warning") or "Cannot write to Sims 4 folder. Error Code 0 will occur on save.",
                severity="CRITICAL",
                auto_fixable=False
            ))
            self.health_score -= 30

        # 9. MacBook Thermal Protection & FPS Limiter
        if self.graphics_diag:
            fps_info = self.graphics_diag.inspect_fps_limit()
            if fps_info["overheating_risk"]:
                self.issues.append(HealthIssue(
                    category="Thermal",
                    title="MacBook Framerate Uncapped (Thermal Throttling Risk)",
                    description="Sims 4 runs at 500+ FPS in menus. Enable VSync and 60/120 FPS limit to protect MacBook hardware.",
                    severity="WARNING",
                    affected_files=[self.graphics_diag.options_ini_path],
                    auto_fixable=True
                ))
                self.health_score -= 10

        # 10. Deep 3D Mesh Inspection (High-poly lag bombs & 0-byte corrupt mods)
        if deep_mesh_scan and self.mods_folder and os.path.isdir(self.mods_folder):
            corrupt_packages: List[str] = []
            for root, _, files in os.walk(self.mods_folder):
                for f in files:
                    if f.lower().endswith(".package"):
                        fp = os.path.join(root, f)
                        try:
                            sz = os.path.getsize(fp)
                            if sz == 0:
                                corrupt_packages.append(fp)
                            elif sz >= 32:
                                with open(fp, "rb") as bf:
                                    if bf.read(4) != b"DBPF":
                                        corrupt_packages.append(fp)
                        except Exception:
                            pass

            if corrupt_packages:
                self.issues.append(HealthIssue(
                    category="Mods",
                    title=f"{len(corrupt_packages)} Corrupt or 0-Byte Packages Found",
                    description="Corrupted package files will trigger game launch crashes or infinite loading.",
                    severity="CRITICAL",
                    affected_files=corrupt_packages,
                    auto_fixable=True
                ))
                self.health_score -= min(25, len(corrupt_packages) * 5)

            if self.mesh_hunter:
                try:
                    mesh_report = self.mesh_hunter.scan_all_packages()
                    lag_count = mesh_report.get("lag_bombs_count", 0)
                    if lag_count > 0:
                        aff_meshes = [b["file"] for b in mesh_report.get("lag_bombs", [])]
                        self.issues.append(HealthIssue(
                            category="Performance",
                            title=f"{lag_count} Extreme High-Poly 3D CC Lag Bombs (>30,000 Polygons)",
                            description="High-poly meshes cause intense stuttering and unified memory exhaustion on Mac.",
                            severity="WARNING",
                            affected_files=aff_meshes,
                            auto_fixable=False
                        ))
                        self.health_score -= min(15, lag_count * 2)
                except Exception:
                    pass

        # Final score bounding
        self.health_score = max(0, min(100, self.health_score))
        if self.health_score >= 85:
            self.health_status = "Healthy Green"
        elif self.health_score >= 50:
            self.health_status = "Warning Yellow"
        else:
            self.health_status = "Critical Red"

        self.last_scan_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return self.get_summary()

    def get_summary(self) -> Dict[str, any]:
        """Formats the current health state into a structured dictionary."""
        crit_count = sum(1 for i in self.issues if i.severity == "CRITICAL")
        warn_count = sum(1 for i in self.issues if i.severity == "WARNING")
        fix_count = sum(1 for i in self.issues if i.auto_fixable)

        return {
            "health_score": self.health_score,
            "health_status": self.health_status,
            "total_issues": len(self.issues),
            "critical_count": crit_count,
            "warning_count": warn_count,
            "auto_fixable_count": fix_count,
            "issues": list(self.issues),
            "last_scan_time": self.last_scan_time,
            "ts4_folder": self.ts4_user_folder
        }

    # ------------------------------------------------------------------------
    # 1-CLICK AUTO-FIX ALL
    # ------------------------------------------------------------------------
    def execute_auto_fix_all(self) -> Dict[str, any]:
        """
        Executes a comprehensive, safe automated repair sequence for macOS:
        1. Creates timestamped Quarantine_WeduGames backup directory.
        2. Fixes Options.ini (enables CC and Script mods).
        3. Flattens deep .ts4script files to Depth 1.
        4. Quarantines 0-byte and corrupted packages.
        5. Hydrates iCloud ghost files.
        6. Purges Metal shader cache and thumbnail caches.
        7. Recovers corrupted save slots from .ver0 backups.
        8. Terminates zombie EA / Sims 4 background processes.
        9. Applies MacBook thermal protection FPS cap (60 FPS default).
        10. Re-runs scan and reports score delta.
        """
        initial_score = self.health_score
        actions_taken: List[str] = []

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        run_quarantine_dir = os.path.join(self.quarantine_folder, f"AutoFix_{timestamp}")
        os.makedirs(run_quarantine_dir, exist_ok=True)

        # 1. Fix Options.ini
        ini_path = os.path.join(self.ts4_user_folder, "Options.ini")
        if os.path.isfile(ini_path):
            try:
                shutil.copy2(ini_path, os.path.join(run_quarantine_dir, "Options.ini.bak"))
                with open(ini_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()

                mod_fixed = False
                if re.search(r"^\s*modsdisabled\s*=\s*1", content, re.MULTILINE):
                    content = re.sub(r"^\s*modsdisabled\s*=\s*1", "modsdisabled = 0", content, flags=re.MULTILINE)
                    mod_fixed = True

                if re.search(r"^\s*scriptmodsenabled\s*=\s*0", content, re.MULTILINE):
                    content = re.sub(r"^\s*scriptmodsenabled\s*=\s*0", "scriptmodsenabled = 1", content, flags=re.MULTILINE)
                    mod_fixed = True

                if mod_fixed:
                    with open(ini_path, "w", encoding="utf-8") as f:
                        f.write(content)
                    actions_taken.append("Enabled Mods and Script Mods in Options.ini")
            except Exception as e:
                actions_taken.append(f"Options.ini repair failed: {e}")

        # 2. Flatten Script Mods
        if self.script_flattener:
            try:
                flat_res = self.script_flattener.flatten_all_violations()
                if flat_res["flattened_count"] > 0:
                    actions_taken.append(f"Flattened {flat_res['flattened_count']} deep script mods to Depth 1")
            except Exception as e:
                actions_taken.append(f"Script flattener failed: {e}")

        # 3. Quarantine 0-Byte and Corrupt Packages
        if self.mods_folder and os.path.isdir(self.mods_folder):
            quarantined_pkgs = 0
            for root, _, files in os.walk(self.mods_folder):
                for f in files:
                    if f.lower().endswith(".package"):
                        fp = os.path.join(root, f)
                        try:
                            is_bad = False
                            sz = os.path.getsize(fp)
                            if sz == 0:
                                is_bad = True
                            elif sz >= 32:
                                with open(fp, "rb") as bf:
                                    if bf.read(4) != b"DBPF":
                                        is_bad = True

                            if is_bad:
                                dest = os.path.join(run_quarantine_dir, f)
                                shutil.move(fp, dest)
                                quarantined_pkgs += 1
                        except Exception:
                            pass
            if quarantined_pkgs > 0:
                actions_taken.append(f"Quarantined {quarantined_pkgs} corrupt/0-byte packages")

        # 4. Hydrate iCloud Ghost Files
        if self.cloud_mgr:
            try:
                hydrated, failed = self.cloud_mgr.hydrate_all_ghosts()
                if hydrated > 0:
                    actions_taken.append(f"Hydrated {hydrated} iCloud ghost files locally")
            except Exception as e:
                actions_taken.append(f"Cloud hydration failed: {e}")

        # 5. Purge Metal Shader Cache & Localthumbcache
        if self.graphics_diag:
            try:
                purged_items, freed_bytes = self.graphics_diag.purge_cache()
                if purged_items > 0:
                    mb = freed_bytes / (1024 * 1024)
                    actions_taken.append(f"Purged {purged_items} Metal shader & cache items ({mb:.1f} MB freed)")
            except Exception as e:
                actions_taken.append(f"Cache purge failed: {e}")

        # 6. Recover Corrupted Save Slots from .ver0
        if self.save_recovery:
            try:
                diag = self.save_recovery.diagnose_all_slots()
                recovered_count = 0
                for cs in diag["corrupted_slots"]:
                    ok, msg = self.save_recovery.rollback_slot(cs.slot_number)
                    if ok:
                        recovered_count += 1
                if recovered_count > 0:
                    actions_taken.append(f"Restored {recovered_count} corrupted save slot(s) from .ver0 backups")
            except Exception as e:
                actions_taken.append(f"Save recovery failed: {e}")

        # 7. Terminate Zombie Background Processes
        try:
            killed_count, logs = ProcessKiller.kill_all_zombies()
            if killed_count > 0:
                actions_taken.append(f"Terminated {killed_count} zombie background process(es)")
        except Exception as e:
            actions_taken.append(f"Process killer failed: {e}")

        # 8. Apply MacBook Thermal Protection FPS Limit (60 FPS default)
        if self.graphics_diag:
            try:
                fps_info = self.graphics_diag.inspect_fps_limit()
                if fps_info["overheating_risk"]:
                    ok, msg = self.graphics_diag.apply_fps_limiter(target_fps=60, force_vsync=True)
                    if ok:
                        actions_taken.append("Applied 60 FPS thermal limiter and VSync in Options.ini")
            except Exception:
                pass

        # Re-run full scan
        new_summary = self.run_full_scan(deep_mesh_scan=False)

        return {
            "initial_score": initial_score,
            "new_score": new_summary["health_score"],
            "new_status": new_summary["health_status"],
            "quarantine_dir": run_quarantine_dir,
            "actions_count": len(actions_taken),
            "actions_taken": actions_taken,
            "remaining_issues": new_summary["total_issues"]
        }

    # Alias for API consistency
    run_health_check = run_full_scan
    run_auto_fix_all = execute_auto_fix_all
