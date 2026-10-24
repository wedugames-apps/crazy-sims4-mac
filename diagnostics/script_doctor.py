"""
==============================================================================
Crazy The Sims 4 Project - Script Doctor & lastException Decoder
==============================================================================
Provides:
- Script mod depth flattener (Sims 4 cannot load .ts4script > 1 folder deep)
- Deep lastException / lastCrash / lastUIException stack trace decoder
"""

import os
import re
import glob
import shutil
from typing import Dict, List, Optional, Tuple


KNOWN_CULPRIT_PATTERNS = [
    (r"ui_cheats|uicheats", "UI Cheats Extension", "Weerbesu",
     "CRITICAL", "UI Cheats is outdated for your game patch. Causes blank UI panels, missing buttons, or game crash."),
    (r"wickedwhims|wonderfulwhims|ww_", "WickedWhims / WonderfulWhims", "TURBODRIVER",
     "HIGH", "WickedWhims animation or tuning out of sync with current game version. Update from official website."),
    (r"mc_cmd_center|mccc", "MC Command Center", "Deaderpool",
     "MEDIUM", "MCCC caught an unhandled game engine tuning exception. Check detailed mc_lastexception.txt."),
    (r"basemental", "Basemental Drugs / Gangs", "Basemental",
     "HIGH", "Basemental script mod interaction error. Update from Basemental CC portal."),
    (r"xml_injector|xmlinjector", "XML Injector", "Scumbumbo",
     "CRITICAL", "XML Injector missing or out of date. Dozens of gameplay mods require this core dependency to function!"),
    (r"betterbuildbuy|bbb_", "Better BuildBuy", "TwistedMexi",
     "HIGH", "Build/Buy catalog UI conflict with current patch. Update from TwistedMexi Patreon."),
    (r"tmex-tool|tool_", "T.O.O.L", "TwistedMexi",
     "MEDIUM", "T.O.O.L object manipulation synchronization error. Update to current version."),
    (r"more_columns|morecolumns", "More CAS Columns", "Weerbesu",
     "HIGH", "Create-A-Sim columns broken by game update. Causes distorted or unusable CAS UI."),
    (r"pandasama|childbirth", "Childbirth Mod", "PandaSama",
     "MEDIUM", "Childbirth animation or rig interaction conflict. Update from PandaSama Patreon."),
    (r"lumpinou|moodpack|relationship_pregnancy", "RPO / Mood Pack", "Lumpinou",
     "MEDIUM", "Relationship / Mood pack tuning out of date. Update Lumpinou mods."),
    (r"lot51_core|lot51", "Lot51 Core Library", "Lot51",
     "HIGH", "Lot51 Core Library missing or out of date. Required by modern interactive CC."),
    (r"sims4communitylib|s4cl", "Sims 4 Community Library", "ColonolNutty",
     "MEDIUM", "S4CL script library out of date. Check mod updates."),
    (r"slider_", "CAS Slider", "Custom Modder",
     "HIGH", "Custom body or facial slider incompatible with patch. Sim deformities will occur."),
]


class FlattenResult(tuple):
    """Dual compatibility result supporting both tuple unpacking (count, logs) and dict indexing."""
    def __new__(cls, moved: int, logs: List[str]):
        return super().__new__(cls, (moved, logs))

    @property
    def flattened_count(self) -> int:
        return self[0]

    @property
    def logs(self) -> List[str]:
        return self[1]

    def __getitem__(self, item):
        if item in ("flattened_count", "moved", "count"):
            return self[0]
        if item in ("logs", "log_messages"):
            return self[1]
        return super().__getitem__(item)

    def get(self, key, default=None):
        if key in ("flattened_count", "moved", "count"):
            return self[0]
        if key in ("logs", "log_messages"):
            return self[1]
        return default


class ScriptModFlattener:
    """Detects and resolves .ts4script nesting depth violations."""

    def __init__(self, mods_folder: str):
        self.mods_folder: str = os.path.abspath(mods_folder)

    def scan_depth_violations(self) -> List[Dict[str, any]]:
        """
        Sims 4 engine rule: .ts4script files can only be at:
        - Depth 0: Mods/mod.ts4script (Valid)
        - Depth 1: Mods/Folder/mod.ts4script (Valid)
        - Depth >= 2: Mods/Folder/Subfolder/mod.ts4script (INVALID - Ignored by game!)
        """
        violations = []
        if not os.path.isdir(self.mods_folder):
            return violations

        for root, _, files in os.walk(self.mods_folder):
            rel_path = os.path.relpath(root, self.mods_folder)
            if rel_path == ".":
                depth = 0
            else:
                parts = rel_path.split(os.sep)
                depth = len(parts)

            for f in files:
                if f.lower().endswith(".ts4script"):
                    if depth > 1:
                        top_folder = rel_path.split(os.sep)[0]
                        violations.append({
                            "filename": f,
                            "current_path": os.path.join(root, f),
                            "current_depth": depth,
                            "rel_dir": rel_path,
                            "top_folder": top_folder,
                            "suggested_dest": os.path.join(self.mods_folder, top_folder, f)
                        })

        return violations

    def flatten_all_violations(self) -> Tuple[int, List[str]]:
        """
        Safely moves all nested .ts4script files to depth 1 (under their respective top folder).
        Returns: (moved_count, log_messages)
        """
        violations = self.scan_depth_violations()
        moved = 0
        logs = []

        for v in violations:
            src = v["current_path"]
            dst = v["suggested_dest"]
            os.makedirs(os.path.dirname(dst), exist_ok=True)

            # Avoid overwriting existing file
            if os.path.exists(dst) and os.path.normcase(src) != os.path.normcase(dst):
                stem, ext = os.path.splitext(v["filename"])
                dst = os.path.join(os.path.dirname(dst), f"{stem}_flattened{ext}")

            try:
                shutil.move(src, dst)
                moved += 1
                logs.append(f"Flattened: {v['filename']} (Depth {v['current_depth']} -> 1)")
            except Exception as e:
                logs.append(f"Failed to move {v['filename']}: {e}")

        return FlattenResult(moved, logs)


class CrashDecoder:
    """Parses and diagnoses lastException and lastCrash logs."""

    def __init__(self, ts4_user_folder: str):
        self.ts4_user_folder: str = os.path.abspath(ts4_user_folder)

    def find_log_files(self) -> List[str]:
        """Finds all exception and crash logs in user folder."""
        patterns = [
            "lastException*.txt",
            "lastCrash*.txt",
            "lastUIException*.txt",
            "mc_lastexception.txt",
        ]
        logs = []
        for pat in patterns:
            logs.extend(glob.glob(os.path.join(self.ts4_user_folder, pat)))
        return sorted(logs, key=os.path.getmtime, reverse=True)

    def analyze_log(self, log_path: str) -> Dict[str, any]:
        """Decodes an exception log file and matches against known mod culprits."""
        result = {
            "file": os.path.basename(log_path),
            "path": log_path,
            "has_error": False,
            "detected_culprits": [],
            "raw_exception_type": None,
            "traceback_snippet": "",
            "summary": "No active exceptions detected."
        }

        if not os.path.isfile(log_path):
            return result

        try:
            with open(log_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            if not content.strip():
                return result

            result["has_error"] = True

            # Match exception types (e.g., AttributeError: ..., KeyError: ...)
            m_err = re.search(r"((?:[a-zA-Z0-9_.]+(?:Error|Exception)):[^\n]+)", content)
            if m_err:
                result["raw_exception_type"] = m_err.group(1).strip()

            # Extract sample traceback
            tb_match = re.search(r"Traceback \(most recent call last\):.*?(?=\n\n|\Z)", content, re.DOTALL)
            if tb_match:
                result["traceback_snippet"] = tb_match.group(0)[:1500]
            else:
                result["traceback_snippet"] = content[:1500]

            # Match against known culprits
            content_lower = content.lower()
            for pattern, mod_name, author, severity, advice in KNOWN_CULPRIT_PATTERNS:
                if re.search(pattern, content_lower):
                    result["detected_culprits"].append({
                        "mod_name": mod_name,
                        "author": author,
                        "severity": severity,
                        "advice": advice
                    })

            if result["detected_culprits"]:
                top = result["detected_culprits"][0]
                result["summary"] = f"Culprit identified: {top['mod_name']} ({top['author']}). {top['advice']}"
            elif result["raw_exception_type"]:
                result["summary"] = f"Generic engine exception: {result['raw_exception_type']}"

        except Exception as e:
            result["error"] = str(e)

        return result

    def get_latest_crash_report(self) -> Optional[Dict[str, any]]:
        """Analyzes the newest exception log file."""
        logs = self.find_log_files()
        if not logs:
            return None
        return self.analyze_log(logs[0])
