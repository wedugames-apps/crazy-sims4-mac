"""
==============================================================================
Crazy Doctor for The Sims 4 (macOS Edition) - EA & TS4 Zombie Process Killer
==============================================================================
Detects and terminates hanging EA background services and frozen Sims 4 processes
on macOS that lock package files and cause launch errors.
"""

import sys
import subprocess
from typing import Dict, List, Optional, Tuple

MACOS_TARGET_PROCESSES = [
    "The Sims 4",
    "EADesktop",
    "EABackgroundService",
    "Origin",
    "OriginClientService",
    "Link2EA",
]

# Windows process names for cross-platform simulation / tests
WINDOWS_TARGET_PROCESSES = [
    "TS4_x64.exe",
    "TS4.exe",
    "EABackgroundService.exe",
    "EADesktop.exe",
    "Origin.exe",
    "OriginClientService.exe",
]


class ProcessKiller:
    """Detects and terminates hanging Sims 4 and EA App background processes on macOS."""

    @staticmethod
    def list_running_targets() -> List[Dict[str, any]]:
        """Scans running system processes for Sims 4 and EA App instances."""
        running = []

        if sys.platform == "darwin":
            try:
                # Query running processes on macOS via ps
                cmd = ["ps", "-ax", "-o", "pid,comm"]
                proc = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                lines = proc.stdout.strip().splitlines()

                for line in lines[1:]:
                    parts = line.strip().split(None, 1)
                    if len(parts) >= 2:
                        pid_str, comm = parts[0], parts[1]
                        for target in MACOS_TARGET_PROCESSES:
                            if target.lower() in comm.lower():
                                running.append({
                                    "name": target,
                                    "pid": pid_str,
                                    "command": comm
                                })
                                break
            except Exception:
                pass

        elif sys.platform == "win32":
            # Windows fallback for developer testing
            try:
                cmd = "tasklist /FO CSV /NH"
                proc = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                lines = proc.stdout.strip().splitlines()

                for line in lines:
                    parts = [p.strip(' "') for p in line.split('","')]
                    if len(parts) >= 2:
                        p_name, p_pid = parts[0], parts[1]
                        for target in WINDOWS_TARGET_PROCESSES + MACOS_TARGET_PROCESSES:
                            if p_name.lower() == target.lower():
                                running.append({
                                    "name": p_name,
                                    "pid": p_pid,
                                    "command": p_name
                                })
                                break
            except Exception:
                pass

        return running

    @classmethod
    def kill_target_process(cls, process_name: str) -> Tuple[bool, str]:
        """Terminates all instances of a target process by name."""
        if sys.platform == "darwin":
            try:
                cmd = ["pkill", "-9", "-f", process_name]
                res = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                if res.returncode == 0:
                    return True, f"Terminated {process_name}."
                return False, f"Could not terminate {process_name}: {res.stderr.strip()}"
            except Exception as e:
                return False, str(e)

        elif sys.platform == "win32":
            try:
                cmd = f"taskkill /F /IM {process_name}"
                res = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=5)
                if res.returncode == 0:
                    return True, f"Terminated {process_name}."
                return False, f"Could not terminate {process_name}: {res.stderr.strip()}"
            except Exception as e:
                return False, str(e)

        return False, "Unsupported platform for process termination."

    @classmethod
    def kill_all_zombies(cls) -> Tuple[int, List[str]]:
        """
        Terminates all detected Sims 4 and EA App background zombie processes.
        Releases file locks on .package files and save directories.
        """
        running = cls.list_running_targets()
        terminated = 0
        logs = []

        seen_names = set()
        for p in running:
            name = p["name"]
            if name not in seen_names:
                seen_names.add(name)
                ok, msg = cls.kill_target_process(name)
                if ok:
                    terminated += 1
                    logs.append(f"Successfully killed {name} (PID {p['pid']})")
                else:
                    logs.append(msg)

        if not running:
            logs.append("No zombie Sims 4 or EA App processes were detected.")

        return terminated, logs
