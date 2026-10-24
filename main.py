"""
==============================================================================
Crazy Doctor for The Sims 4 (macOS Edition) - Application Entry Point
==============================================================================
Launch the All-In-One Commercial Diagnostic, Optimizer, and Auto-Fixer Suite
for The Sims 4 on macOS (Universal2: Apple Silicon M1/M2/M3/M4 & Intel x86_64).
Supports modern CustomTkinter desktop GUI and headless CLI modes.
"""

import os
import sys
import argparse
import multiprocessing

multiprocessing.freeze_support()

# Ensure project root is in sys.path
if getattr(sys, "frozen", False):
    PROJECT_ROOT = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
else:
    PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Safe console encoding configuration
if sys.stdout and hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass
if sys.stderr and hasattr(sys.stderr, "reconfigure"):
    try:
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass


def run_cli_scan(ts4_folder=None, auto_fix=False):
    """Executes a terminal-based diagnostic scan or auto-fix on macOS."""
    from diagnostics.health_suite import MasterHealthSuite

    print("==================================================================")
    print("⚡ CRAZY DOCTOR FOR THE SIMS 4 - WEDUGAMES (MACOS DIAGNOSTICS)")
    print("==================================================================")

    suite = MasterHealthSuite(ts4_folder)
    print(f"Target The Sims 4 Folder: {suite.ts4_user_folder or 'Not Found!'}")
    print("Running multi-point native macOS diagnostic scan...")

    summary = suite.run_full_scan(deep_mesh_scan=True)

    print("\n------------------------- SCAN RESULTS -------------------------")
    print(f"Health Score  : {summary['health_score']}/100")
    print(f"Status        : {summary['health_status']}")
    print(f"Total Issues  : {summary['total_issues']} (Critical: {summary['critical_count']}, Warnings: {summary['warning_count']})")
    print(f"Auto-Fixable  : {summary['auto_fixable_count']} issues")

    if summary["issues"]:
        print("\nActive Findings:")
        for idx, issue in enumerate(summary["issues"], 1):
            print(f" {idx}. [{issue.severity}] [{issue.category}] {issue.title}")
            print(f"    {issue.description}")
            if issue.affected_files:
                print(f"    Affected ({len(issue.affected_files)} files): {issue.affected_files[0]}")
    else:
        print("\n✓ No issues found. System is completely healthy!")

    if auto_fix:
        print("\n------------------------ AUTO-FIX ALL -------------------------")
        print("Executing automated repair sequence with safe quarantine backup...")
        fix_res = suite.execute_auto_fix_all()
        print(f"Initial Score : {fix_res['initial_score']} ➔ New Score: {fix_res['new_score']} ({fix_res['new_status']})")
        print(f"Backup Dir    : {fix_res['quarantine_dir']}")
        print(f"Actions Taken ({fix_res['actions_count']}):")
        for act in fix_res["actions_taken"]:
            print(f" • {act}")

    print("\n==================================================================")
    try:
        if sys.stdout and hasattr(sys.stdout, "flush"):
            sys.stdout.flush()
    except Exception:
        pass


def run_cli_doctor(complaint: str = None, image_path: str = None, briefing: bool = False, ts4_folder: str = None):
    """Executes WeduGames Doctor diagnosis from CLI (Crazy Core)."""
    from diagnostics.health_suite import MasterHealthSuite
    from core.doctor_core import CrazySimsDoctor

    doc = CrazySimsDoctor()
    suite = MasterHealthSuite(ts4_folder)

    print("==================================================================")
    print("🩺 CRAZY DOCTOR FOR THE SIMS 4 - WEDUGAMES (MACOS CLI)")
    print("==================================================================")
    status_str = "Online (Crazy Core)" if doc.is_api_configured() else "Offline Knowledge Engine"
    print(f"Engine Mode: {status_str}\n")

    if image_path:
        print(f"Analyzing Screenshot: {image_path}\n")
        res = doc.diagnose_image(image_path, user_notes=complaint or "")
        print("Doctor Vision Diagnosis:")
        print(res.get("diagnosis", ""))
        rec = res.get("recommended_action")
        if rec:
            print(f"\n⚡ Recommended Action: {rec.get('label')} ({rec.get('action')})")
            print(f"   Reason: {rec.get('reason')}")
    elif complaint:
        print(f"Player Query: \"{complaint}\"\n")
        res = doc.diagnose_text(complaint)
        print("Doctor Diagnosis:")
        print(res.get("diagnosis", ""))
        rec = res.get("recommended_action")
        if rec:
            print(f"\n⚡ Recommended Action: {rec.get('label')} ({rec.get('action')})")
            print(f"   Reason: {rec.get('reason')}")

    if briefing:
        print("Running diagnostic scan for WeduGames Doctor Briefing...")
        summary = suite.run_full_scan(deep_mesh_scan=False)
        res = doc.generate_doctor_briefing(summary)
        print("\n" + res.get("briefing", ""))

    print("\n==================================================================")
    try:
        if sys.stdout and hasattr(sys.stdout, "flush"):
            sys.stdout.flush()
    except Exception:
        pass


def run_cli_license(activate_key: str = None, check_only: bool = False):
    """Handles license activation and auto-unlock checks from terminal."""
    from core.license import MacLicenseManager

    print("==================================================================")
    print("🔐 UNIFIED 1-KEY MACOS REGISTRATION SYSTEM - WEDUGAMES")
    print("==================================================================")
    hwid = MacLicenseManager.get_macos_hwid()
    print(f"macOS Hardware UUID: {hwid}")
    paths = MacLicenseManager.get_cache_paths()
    print(f"Primary Cache Path : {paths[0]}")

    if activate_key:
        print(f"\nActivating License Key: {activate_key} ...")
        ok, msg, data = MacLicenseManager.activate_license(activate_key)
        if ok:
            print(f"✅ Success: {msg}")
            print(f"   Key: {data.get('key')}")
            print(f"   Status: {data.get('status')}")
            print(f"   Devices Registered: {len(data.get('devices', []))}/3")
        else:
            print(f"❌ Failed: {msg}")
        return

    unlocked, msg, cache = MacLicenseManager.check_auto_unlock()
    print(f"\nAuto-Unlock Status : {'UNLOCKED' if unlocked else 'LOCKED'}")
    print(f"Message            : {msg}")
    if unlocked:
        print(f"Active Key         : {cache.get('key')}")
        print(f"Devices Registered : {len(cache.get('devices', []))}/3")
    print("==================================================================")


def main():
    parser = argparse.ArgumentParser(description="Crazy Doctor for The Sims 4 (macOS Edition)")
    parser.add_argument("--scan", action="store_true", help="Run command-line full scan without GUI")
    parser.add_argument("--fix", action="store_true", help="Run 1-Click Auto-Fix All from terminal")
    parser.add_argument("--briefing", action="store_true", help="Generate WeduGames Doctor Briefing summary from scan")
    parser.add_argument("--ask", type=str, default=None, help="Ask the Sims 4 WeduGames Doctor to diagnose a symptom")
    parser.add_argument("--image", type=str, default=None, help="Path to Sims 4 screenshot image to diagnose")
    parser.add_argument("--path", type=str, default=None, help="Custom path to Electronic Arts/The Sims 4 folder")
    parser.add_argument("--activate", type=str, default=None, help="Activate WG-TS4M-XXXX-XXXX license key")
    parser.add_argument("--check-license", action="store_true", help="Check macOS license cache and auto-unlock status")
    args = parser.parse_args()

    if args.activate or args.check_license:
        run_cli_license(activate_key=args.activate, check_only=args.check_license)
        return

    if args.ask or args.image or args.briefing:
        run_cli_doctor(complaint=args.ask, image_path=args.image, briefing=args.briefing, ts4_folder=args.path)
        return

    if args.scan or args.fix:
        run_cli_scan(ts4_folder=args.path, auto_fix=args.fix)
        return

    # Launch Modern CustomTkinter GUI
    from ui.app_window import AppWindow

    app = AppWindow(ts4_folder=args.path)
    app.mainloop()


if __name__ == "__main__":
    main()
