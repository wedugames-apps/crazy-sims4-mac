"""
==============================================================================
Crazy Doctor for The Sims 4 (macOS Edition) - Localization (i18n) Engine
==============================================================================
High-performance native bilingual engine (Bahasa Indonesia & English):
- Apple Metal Graphics Engine & Metal shader cache management
- MacBook & iMac thermal limiter (60Hz Retina / 120Hz Liquid Retina ProMotion)
- iCloud Drive eviction & ghost file hydrator
- macOS Full Disk Access & App Sandbox diagnostics
- Unified 1-Key macOS Registration & Auto-Unlock indicators
- WeduGames Doctor & Crazy Core consultation
- Persistent language selection in doctor_config.json
- Zero occurrences of prohibited legacy terminology
"""

import os
import sys
import json
from typing import Dict, Any, Callable, List, Optional

SUPPORTED_LANGUAGES = ["id", "en"]
DEFAULT_LANGUAGE = "id"


TRANSLATIONS: Dict[str, Dict[str, str]] = {
    "en": {
        # App Window & Header
        "app_title": "Crazy Doctor for The Sims 4 (macOS Edition) - WeduGames",
        "header_brand_title": "⚡ CRAZY DOCTOR",
        "header_brand_subtitle": " FOR THE SIMS 4 (MAC)",
        "engine_core_online": "Crazy Core: Online",
        "engine_core_offline": "Crazy Core: Standby",
        "btn_change_folder": "Change Folder",
        "folder_not_found": "Folder Not Found",
        "lang_toggle_btn": "🌐 🇬🇧 EN | ID",
        "lang_btn_text": "🌐 🇬🇧 EN",
        "folder_dialog_title": "Select The Sims 4 User Folder (containing Mods, saves, Options.ini)",
        "folder_updated_title": "Folder Updated",
        "folder_updated_msg": "Successfully set The Sims 4 folder to:\n{path}",

        # Sidebar Navigation
        "nav_main_heading": "MAIN NAVIGATION",
        "nav_dashboard": "📊  Dashboard",
        "nav_doctor_core": "🩺  WeduGames Doctor",
        "nav_doctor": "🩺  Doctor & Scripts",
        "nav_graphics": "🎮  Metal & Graphics",
        "nav_mods": "👗  Mods & 3D CC",
        "nav_saves": "💾  Saves & Tray",
        "nav_system": "⚙️  macOS System & VIP",
        "vip_badge_title": "MACOS COMMERCIAL EDITION",
        "vip_badge_version": "v1.0.0 Universal2\nWeduGames Engine",

        # Dashboard Tab
        "dash_score_title": "HEALTH SCORE",
        "dash_status_healthy": "HEALTHY GREEN",
        "dash_status_warning": "WARNING YELLOW",
        "dash_status_critical": "CRITICAL RED",
        "dash_title": "THE SIMS 4 MACOS ALL-IN-ONE DOCTOR",
        "dash_desc": "Autonomous Diagnostics, Metal VRAM Optimizer & Safe Quarantine Auto-Fix.",
        "dash_last_scan_never": "Last Scan: Never",
        "dash_last_scan_time": "Last Scan: {time}",
        "dash_btn_scan": "⚡ 1-CLICK FULL SCAN",
        "dash_btn_scanning": "SCANNING...",
        "dash_btn_autofix": "🛠️ AUTO-FIX ALL ISSUES",
        "dash_btn_fixing": "REPAIRING...",
        "dash_card_crit_title": "CRITICAL ISSUES",
        "dash_card_crit_desc": "Crashes, 0-byte corrupt mods, script depth violations, iCloud ghosts",
        "dash_card_warn_title": "WARNINGS & LAG BOMBS",
        "dash_card_warn_desc": "High-poly 3D meshes, missing parent meshes, Metal cache bloat",
        "dash_card_healthy_title": "HEALTHY SYSTEMS",
        "dash_card_healthy_desc": "Options.ini, active saves, Metal configuration, macOS permissions",
        "dash_card_healthy_optimal": "OPTIMAL",
        "dash_log_title": "🔍 DIAGNOSTIC LOG & ACTIVE FINDINGS",
        "dash_issues_count": "{count} Issues Found",
        "dash_issues_detected": "{count} Issues Detected",
        "dash_empty_state": "✨ No scan has been run yet. Click '1-CLICK FULL SCAN' above to diagnose.",
        "dash_all_clean": "🎉 Outstanding! Your The Sims 4 macOS installation is 100% clean, optimal, and healthy!",
        "dash_autofixable_tag": "AUTO-FIXABLE ✓",
        "dash_dialog_scan_error_title": "Scan Error",
        "dash_dialog_scan_error_msg": "Encountered an error while scanning: {error}",
        "dash_dialog_autofix_title": "Auto-Fix All",
        "dash_dialog_autofix_confirm": "Auto-Fix All will perform systematic repairs (flatten nested scripts, purge Metal shader cache, hydrate iCloud placeholders, apply thermal limit, terminate zombie processes, and safeguard saves).\n\nA safe backup checkpoint will be created in 'Quarantine_WeduGames'. Proceed?",
        "dash_dialog_autofix_done_title": "Auto-Fix Complete!",
        "dash_dialog_autofix_done_msg": "Auto-Fix successfully finished!\n\nHealth Score: {initial_score} ➔ {new_score} ({new_status})\nActions Executed ({actions_count}):{actions_str}\n\nBackup Location:\n{quarantine_dir}",
        "dash_dialog_autofix_err_title": "Auto-Fix Error",
        "dash_dialog_autofix_err_msg": "Auto-Fix encountered an error: {error}",

        # Doctor Tab
        "doc_sec_script_title": "📜 SCRIPT MOD DEPTH FLATTENER",
        "doc_btn_flatten": "⚡ Flatten All Deep Scripts",
        "doc_script_desc": "Sims 4 cannot load .ts4script files placed 2+ subfolders deep. Safely moves them to Depth 1.",
        "doc_script_status_default": "Sims 4 cannot load .ts4script files placed 2+ subfolders deep. Safely moves them to Depth 1.",
        "doc_script_status_done": "✓ Last Action: Flattened {count} script mod(s) to Depth 1. Game engine can now recognize them!",
        "doc_sec_crash_title": "💥 LASTEXCEPTION & CRASH TRACE DECODER",
        "doc_btn_analyze_crash": "🔎 Analyze Latest Crash Log",
        "doc_crash_placeholder": "Click 'Analyze Latest Crash Log' to parse recent lastException/lastCrash files and identify the culprit mod...",
        "doc_sec_corrupt_title": "🗑️ 0-BYTE & CORRUPT MOD ISOLATOR",
        "doc_btn_isolate": "🛡️ Quarantine Corrupted Mods",
        "doc_corrupt_desc": "Scans for 0-byte packages, aborted downloads, and broken headers, safely moving them to Quarantine_WeduGames.",
        "doc_corrupt_status_default": "Scans for 0-byte packages, aborted downloads, and broken headers, safely moving them to Quarantine_WeduGames.",
        "doc_corrupt_status_done": "✓ Last Action: Quarantined {count} broken package(s).",
        "doc_notice_mods_missing": "Mods folder not found.",
        "doc_notice_user_missing": "User folder not found.",
        "doc_flatten_clean": "All script mods (.ts4script) are at safe depths (Depth 0 or 1).",
        "doc_flatten_success": "Successfully flattened {count} script mod(s) to Depth 1!{log_str}",
        "doc_crash_clean": "No lastException or lastCrash logs found. Your game logs are clean!",
        "doc_corrupt_clean": "No 0-byte or corrupted package files found in your Mods folder.",
        "doc_corrupt_success": "Successfully quarantined {count} corrupted 0-byte package(s) to:\n{dir}",

        # Graphics & GPU Tab (Metal API)
        "gfx_sec_dx_title": "⚡ APPLE METAL GRAPHICS ENGINE (MACOS)",
        "gfx_dx_current": "Current Renderer: {mode}",
        "gfx_dx_checking": "Current Renderer: Checking...",
        "gfx_dx_desc": "Apple Metal API provides low-overhead GPU hardware acceleration, cooler operating temperatures, and battery efficiency on macOS.",
        "gfx_btn_dx11": "Metal Renderer Active (macOS Native)",
        "gfx_btn_dx9": "Legacy Mode",
        "gfx_sec_cache_title": "🧹 METAL SHADER & THUMBNAIL CACHE PURGER",
        "gfx_btn_purge": "⚡ 1-Click Purge Metal Cache",
        "gfx_cache_inspecting": "Inspecting Metal shader caches...",
        "gfx_cache_summary": "Accumulated Cache: {size} ({count} items)",
        "gfx_cache_desc": "Purging localthumbcache and native Metal shader cache (~/Library/Caches/com.ea.TheSims4/) clears pink visual glitches, outdated UI artifacts, and stutter.",
        "gfx_sec_fps_title": "❄️ MACBOOK THERMAL LIMITER (60Hz / 120Hz ProMotion)",
        "gfx_fps_desc": "Sims 4 menus and loading screens run uncapped (500+ FPS), causing excessive fan noise and thermal throttling on MacBooks. Cap framerate to protect hardware:",
        "gfx_btn_cap_fps": "Cap at {fps} FPS",
        "gfx_fps_status_active": "✓ MacBook Thermal Protection Active: Framerate capped at {limit}",
        "gfx_fps_status_uncapped": "⚠️ Framerate uncapped. MacBook is vulnerable to thermal throttling and loud fans.",
        "gfx_cache_purged_title": "Metal Cache Purged",
        "gfx_cache_purged_msg": "Successfully purged {count} cache items!\nFreed {size} of disk storage.",

        # Mods & 3D CC Tab
        "mods_sec_mesh_title": "📐 3D MESH PROFILER & LAG-BOMB DETECTOR",
        "mods_btn_mesh_scan": "🔍 Scan CC Meshes",
        "mods_mesh_desc": "Inspects GEOM 3D meshes for extreme polycounts (>30,000 polygons) and missing parent meshes.",
        "mods_mesh_placeholder": "Click 'Scan CC Meshes' to analyze 3D geometry in your Mods folder...",
        "mods_mesh_scanning": "Scanning package files...",
        "mods_mesh_scanning_bg": "Profiling 3D meshes in background...",
        "mods_mesh_complete": "Scan complete: {lag_bombs} lag bombs, {orphans} orphan recolors found.",
        "mods_sec_townie_title": "👗 NPC TOWNIE CC SANITIZER (AllowForRandom = 0)",
        "mods_btn_townie": "🚫 Sanitize All Townie CC",
        "mods_btn_townie_running": "SANITIZING...",
        "mods_townie_desc": "Stops random NPC townies from spawning in wild CC hairs, broken alpha outfits, or weird accessories.",
        "mods_townie_status_done": "✓ Sanitized {pkgs} packages ({casps} CAS parts).",
        "mods_townie_confirm_title": "Sanitize Townie CC",
        "mods_townie_confirm_msg": "This will scan CAS packages and disable the AllowForRandom bit (preventing townies from wearing them).\n\nYou will still be able to wear and select these items in CAS for your played Sims as normal. Continue?",
        "mods_townie_done_title": "Townie Sanitization Complete",
        "mods_townie_done_msg": "Successfully sanitized {pkgs} packages and disabled AllowForRandom on {casps} parts!\nNPC townies will no longer generate wearing these items.",
        "mods_sec_tex_title": "🖼️ TEXTURE OPTIMIZER (Lanczos Downsampler)",
        "mods_btn_opt_tex": "⚡ Downsample 4K Textures to 2K",
        "mods_tex_desc": "Oversized 4K/8K uncompressed CC textures choke GPU VRAM and unified memory on macOS. Downsample to crisp 2K with high-fidelity Lanczos resampling.",
        "mods_tex_status_done": "✓ Downsampled {count} textures, freed {freed}.",
        "mods_tex_confirm_title": "Lanczos Downsampler",
        "mods_tex_confirm_msg": "Downsampling oversized 4K/8K textures to 2K Lanczos saves up to 60% GPU unified memory and prevents stutter.\nVisual sharpness is preserved. Continue?",
        "mods_tex_done_title": "Texture Optimization Complete",
        "mods_tex_done_msg": "Successfully downsampled {count} textures to 2K Lanczos!\nSaved {freed} of memory.",
        "mods_sec_5050_title": "⚖️ 50/50 BINARY SEARCH TROUBLESHOOTING AUTOMATOR",
        "mods_5050_step_inactive": "Step 0: Inactive",
        "mods_5050_step_progress": "Step {step}: Testing {active} mods ({suspects} remaining)",
        "mods_5050_step_isolated": "CULPRIT ISOLATED!",
        "mods_5050_desc_default": "Automatically isolates mysterious bugs, crashes, or glitches by bisecting your mods into halves until the offending file is found.",
        "mods_5050_desc_progress": "50/50 Session in progress! Half your mods are active in-game; half are staged aside. Test your game, then choose below:",
        "mods_5050_desc_isolated": "🎯 Culprit mod isolated:\n{mod}",
        "mods_btn_5050_start": "Start New 50/50 Session",
        "mods_btn_5050_broken": "❌ Error Still Occurs",
        "mods_btn_5050_clean": "✅ Game Runs Cleanly",
        "mods_btn_5050_cancel": "Restore All & Cancel",

        # Saves & Tray Tab
        "saves_sec_saves_title": "💾 SAVE ARCHIVIST & 1-CLICK ROLLING ROLLBACK",
        "saves_btn_snapshot": "📸 Create Snapshot",
        "saves_btn_purge_ver": "🧹 Purge Stale .ver Backups",
        "saves_sec_tray_title": "📦 TRAY LIBRARY & CC DEPENDENCY INSPECTOR",
        "saves_btn_scan_tray": "🔍 Scan Tray Library",
        "saves_btn_export_bundle": "📦 Export CC Bundle (.zip)",
        "saves_tray_desc": "Inspects Households and Lots in your Tray folder to detect missing CC (bald Sims or missing walls).",
        "saves_tray_placeholder": "Click 'Scan Tray Library' to analyze saved Sims and Lots...",
        "saves_tray_scanning": "Scanning library items and cross-referencing Mods folder...",
        "saves_tray_status_done": "✓ Successfully scanned {count} library items.",
        "saves_btn_rollback": "↺ Rollback to .ver0",
        "saves_status_corrupted": "CORRUPTED",
        "saves_status_healthy": "HEALTHY",
        "saves_not_found": "Saves folder not found.",
        "saves_no_slots": "No save slot files found in saves/ folder.",
        "saves_slot_label": "Slot {dec} ({hex})",
        "saves_slot_autosave": " [AUTOSAVE]",
        "saves_slot_details": "Size: {size} | Last Played: {last_played} | Backups: {ver_count} versions (.ver0-.ver4)",
        "saves_rollback_confirm_title": "Confirm Rollback",
        "saves_rollback_confirm_msg": "Are you sure you want to rollback Slot {slot} to .ver0?\n\nAn automatic pre-restore checkpoint will be captured before restoration.",
        "saves_rollback_done_title": "Rollback Complete",
        "saves_rollback_err_title": "Rollback Failed",
        "saves_snapshot_prompt_title": "Create Snapshot",
        "saves_snapshot_prompt_msg": "Enter a name/label for this save checkpoint:",
        "saves_snapshot_done_title": "Snapshot Created",
        "saves_snapshot_done_msg": "Successfully captured checkpoint:\n{msg}",
        "saves_snapshot_err_title": "Snapshot Failed",
        "saves_purge_confirm_title": "Purge Stale Backups",
        "saves_purge_confirm_msg": "This will delete older rolling backups (.ver1 - .ver4), while RETAINING .ver0 as an emergency recovery point.\n\nProceed to free disk space?",
        "saves_purge_done_title": "Purge Complete",
        "saves_purge_done_msg": "Deleted {deleted} stale backup files.\nFreed {freed} of storage!",

        # System & VIP Tab (macOS)
        "sys_sec_ghost_title": "☁️ ICLOUD DRIVE GHOST FILE HYDRATOR",
        "sys_btn_hydrate": "⚡ Force Hydrate All Files",
        "sys_ghost_desc": "iCloud Drive 'Optimize Mac Storage' evicts packages into .icloud ghost files, freezing Sims 4 on load. Forces all mods & saves to download locally.",
        "sys_ghost_found": "⚠️ Found {count} unhydrated iCloud ghost files! Game may freeze on load.",
        "sys_ghost_clean": "✓ All files in Mods and saves are 100% hydrated and locally available on disk.",
        "sys_sec_split_title": "🔀 SPLIT DOCUMENTS FOLDER MERGER",
        "sys_btn_merge": "🔗 Merge Secondary Folder",
        "sys_split_desc": "Detects if iCloud Drive created a split 'The Sims 4' folder across Local ~/Documents and CloudDocs, safely merging files.",
        "sys_split_detected": "⚠️ Split detected across {count} locations (e.g. Local Documents & iCloud Documents).",
        "sys_split_clean": "✓ No split Documents folders detected. All game data is unified.",
        "sys_sec_zombie_title": "🧟 MACOS EA APP & TS4 PROCESS KILLER",
        "sys_btn_kill_zombies": "💀 Kill All Zombie Processes",
        "sys_zombie_desc": "Terminates background EA Desktop and frozen The Sims 4 instances that lock package files and cause launch errors.",
        "sys_zombie_detected": "⚠️ {count} active background processes detected: {names}",
        "sys_zombie_clean": "✓ No hanging background processes detected. File locks are clear.",
        "sys_sec_cfa_title": "🛡️ MACOS FULL DISK ACCESS & PERMISSIONS",
        "sys_cfa_checking": "Checking macOS file permissions...",
        "sys_cfa_desc": "macOS App Sandbox & Privacy requires write access to Documents/Electronic Arts/The Sims 4 to save game data without Error Code 0.",
        "sys_cfa_enabled_ok": "✓ Full Disk Access & Write Permissions are OK.",
        "sys_cfa_enabled_blocked": "⚠️ Write permission RESTRICTED! Grant 'Full Disk Access' in macOS System Settings > Privacy & Security to prevent Error 0.",
        "sys_cfa_disabled_ok": "✓ Folder write permissions are unrestricted.",
        "sys_sec_vip_title": "🚀 UNIFIED 1-KEY MAC REGISTRATION & VIP LAUNCHER",
        "sys_btn_launch": "▶️ Launch The Sims 4.app",
        "sys_exe_searching": "Searching for The Sims 4.app bundle...",
        "sys_exe_detected": "✓ Detected: {exe}",
        "sys_exe_not_found": "⚠️ The Sims 4.app bundle not automatically found in /Applications.",
        "sys_hydrate_done_title": "Hydration Complete",
        "sys_hydrate_done_msg": "Successfully hydrated {success} cloud file(s) locally. Failed: {failed}.",
        "sys_merge_confirm_title": "Confirm Merge",
        "sys_merge_confirm_msg": "Merge files from secondary folder:\n{src}\n\ninto active primary folder:\n{dst}?\n\nNewer files will not be overwritten.",
        "sys_merge_done_title": "Merge Complete",
        "sys_zombie_done_title": "Process Killer",
        "sys_zombie_done_msg": "Terminated {count} process(es):{logs}",

        # WeduGames Doctor Tab
        "doc_banner_title": "🩺 WEDUGAMES DOCTOR & MULTIMODAL ASSISTANT",
        "doc_banner_desc": "Autonomous Diagnostic Engine (Crazy Core) • Visual Screenshot OCR, Drag & Drop & 1-Click Healing.",
        "doc_btn_briefing": "🩺 WeduGames Doctor Briefing",
        "doc_key_label": "Engine Key:",
        "doc_placeholder_key": "Enter key or paste multiple...",
        "doc_btn_save_key": "➕ Add/Save",
        "doc_btn_pool": "🔑 Pool ({count}) {arrow}",
        "doc_btn_sync_cloud": "🌐 Cloud Sync",
        "doc_model_label": "Model:",
        "doc_pool_title": "🔑 ENGINE KEY POOL (Load Balancing & Failover)",
        "doc_pool_stats": "Active Keys: {count} | Source: {source} | Strategy: Round-Robin",
        "doc_pool_paste_label": "📋 Paste multiple keys (one per line, comma or space separated):",
        "doc_btn_import_batch": "📥 Import All Keys to Pool",
        "doc_btn_clear_input": "🧹 Clear Input",
        "doc_btn_clear_pool": "🗑️ Clear Entire Pool",
        "doc_btn_revert_cloud": "🌐 Revert to Cloud Pool",
        "doc_btn_close_panel": "✕ Close Panel",
        "doc_active_keys_queue": "Active Keys in Pool (Round-Robin Execution Queue):",
        "doc_action_rec_title": "⚡ WEDUGAMES ACTION RECOMMENDED: {label}",
        "doc_btn_execute_now": "⚡ Execute WeduGames Solution",
        "doc_btn_dismiss": "✕ Dismiss",
        "doc_btn_attach": "📎 Attach",
        "doc_btn_paste": "📋 Paste",
        "doc_input_placeholder": "Describe your issue, error code, or ask for guidance... (Press Enter to Send)",
        "doc_btn_send": "Send 🚀",
        "doc_btn_thinking": "Thinking...",
        "doc_btn_assessing": "Assessing...",
        "doc_badge_doctor": "🩺 WeduGames Doctor",
        "doc_badge_player": "👤 Player",
        "doc_welcome_text": (
            "👋 **Hello! I am your WeduGames Doctor & Systems Specialist for macOS.**\n\n"
            "How can I help you restore your game to optimal condition today?\n"
            "• **Visual Glitches**: Attach a screenshot of Error 102/109, red-and-white question marks, pink Metal shaders, or stretched Sims.\n"
            "• **Symptom Descriptions**: Describe any game freeze, infinite loading, or save problems.\n"
            "• **Automated Healing**: When I identify the cause, I will provide a **1-Click Solution** you can execute immediately!\n\n"
            "_💡 Tip: Attach screenshots via **Browse**, **Drag & Drop** anywhere into this tab, or **Cmd+V Paste** from clipboard._"
        ),
        "doc_status_cloud": "🌐 Cloud Pool: {count} Keys Active (WeduGames VIP)",
        "doc_status_custom": "👤 Custom Key: {count} Keys Active",
        "doc_status_balanced": "🟢 {count} Keys Active (Load-Balanced)",
        "doc_status_single": "🟢 1 Key Active (Crazy Core)",
        "doc_status_offline": "🟡 Offline Heuristic Mode (0 Keys)",
        "doc_status_online_badge": "● WeduGames Doctor Online",
        "doc_status_offline_badge": "● WeduGames Doctor Offline (Heuristic Mode)",
        "doc_status_badge_tooltip": "Autonomous Cloud Neural Network Connected (WeduGames VIP Zero-Setup)",

        # Common
        "common_notice": "Notice",
        "common_error": "Error",
        "common_success": "Success",
        "common_none": "None.",
        "common_warning": "Warning",

        # Doctor Tab Dialogs
        "doc_dialog_script_title": "Script Doctor",
        "doc_dialog_isolate_title": "Isolator",
        "doc_dialog_isolate_done_title": "Isolator Complete",
        "doc_crash_log_file": "LOG FILE: {file}",
        "doc_crash_summary": "SUMMARY: {summary}",
        "doc_crash_culprits": "IDENTIFIED CULPRITS:",
        "doc_crash_culprit_item": " • Mod: {mod} (Author: {author}) - Severity: {sev}\n   Recommendation: {advice}",
        "doc_crash_engine_err": "ENGINE ERROR: {err}",
        "doc_crash_traceback": "TRACEBACK PREVIEW:",

        # Graphics Tab Dialogs
        "gfx_dialog_dx_title": "Metal Graphics Engine",
        "gfx_dialog_dx_success": "Successfully configured Metal API for {mode}!",
        "gfx_dialog_dx_error": "Failed to configure Metal: {error}",
        "gfx_dialog_fps_title": "MacBook FPS Limiter",
        "gfx_dialog_fps_success": "Framerate limit of {fps} FPS applied successfully! Thermal protection active.",
        "gfx_dialog_fps_error": "Failed to apply FPS limit: {error}",

        # Mods Tab Dialogs
        "mods_mesh_res_header": "3D Mesh Analysis Results:\n",
        "mods_mesh_res_summary": "Scanned {pkg_count} packages ({mesh_count} GEOM meshes):\n",
        "mods_mesh_res_lag_bombs": "⚠️ HIGH-POLY LAG BOMBS (>30,000 triangles):",
        "mods_mesh_res_orphans": "⚠️ ORPHAN RECOLORS (Missing base mesh in Mods/):",
        "mods_mesh_res_clean": "✓ All scanned 3D meshes are healthy and have valid parent base meshes.",
        "mods_5050_dialog_title": "50/50 Automator",

        # Saves & Tray Tab Dialogs
        "saves_tray_none_found": "No Tray items (.trayitem) found in your Tray/ folder.",
        "saves_tray_scanned_header": "Scanned {count} Library Items from Tray/:\n",
        "saves_tray_creator": "  Creator: {creator}",
        "saves_tray_found_cc": "  Found CC Packages: {count}",
        "saves_tray_missing_cc": "  ⚠️ Missing Custom Items: {count} (Sim/Lot may look naked/empty)",
        "saves_export_bundle_title": "Export Bundle",
        "saves_export_bundle_first_scan": "Please click 'Scan Tray Library' first to index your items.",
        "saves_export_bundle_dialog_title": "Export CC Bundle for '{name}'",
        "saves_export_bundle_done_title": "Export Complete",
        "saves_export_bundle_done_msg": "Successfully exported '{name}' and all matched CC packages into:\n{path}",
        "saves_export_bundle_err_title": "Export Failed",
        "saves_export_bundle_err_msg": "Failed to export CC bundle archive.",

        # System Tab Dialogs
        "sys_cfa_non_windows": "macOS platform.",
        "sys_dialog_select_exe_title": "Select The Sims 4.app",
        "sys_game_launched_title": "Game Launched",
        "sys_game_launched_msg": "Launching The Sims 4:\n{exe}",
        "sys_launch_err_title": "Launch Error",
        "sys_launch_err_msg": "Failed to launch game: {err}",
        "sys_merge_none_found": "No split Documents folder was found.",
        "sys_merge_no_secondary": "No secondary folder identified.",

        # WeduGames Doctor Tab Dialogs & Extras
        "doc_btn_remove_attach": "✕ Remove",
        "doc_chat_request_briefing_scan": "Please run a scan and generate a WeduGames Doctor Briefing on my Sims 4 health.",
        "doc_chat_doctor_assessing": "Initiating health assessment and synthesizing WeduGames Doctor Briefing...",
        "doc_chat_request_briefing": "Generate a WeduGames Doctor Briefing based on my latest scan results.",
        "doc_chat_screenshot_submitted": "[Screenshot submitted for diagnosis]",
        "doc_btn_executing_action": "Executing Solution...",
        "doc_action_executed_success": "✅ **Solution Executed Successfully [{label}]:**\n\n{msg}",
        "doc_action_executed_failed": "❌ **Solution Execution Failed [{label}]:**\n\n{msg}",
        "doc_action_done_title": "WeduGames Solution Executed",
        "doc_action_err_title": "Execution Failed",
        "doc_key_dialog_title": "Crazy Core Engine",
        "doc_key_err_min_length": "API key must be longer than 10 characters.",
        "doc_key_err_enter_valid": "Please enter a valid API key.",
        "doc_key_saved_msg": "Custom API key active and ready!\nMasked: {key}",
        "doc_key_config_updated": "Engine configuration updated.\nActive Keys: {count}",
        "doc_batch_title": "Batch Import",
        "doc_batch_paste_first": "Please paste one or more API keys into the textbox.",
        "doc_batch_none_valid": "No valid keys found. Each key must be longer than 10 characters.",
        "doc_clear_pool_title": "Confirm Clear Pool",
        "doc_clear_pool_confirm": "Are you sure you want to remove ALL API keys from the pool?",
        "doc_copied_title": "Copied",
        "doc_copied_msg": "API Key copied to clipboard.",
        "doc_cloud_sync_title": "Cloud Sync",
        "doc_cloud_sync_success": "Cloud keys synchronized successfully!\nActive Pool Count: {count}",
        "doc_cloud_pool_restored_title": "Cloud Pool Restored",
        "doc_clipboard_title": "Clipboard",
        "doc_clipboard_none_found": "No image found in clipboard.",
        "doc_clipboard_err_title": "Clipboard Error",
        "doc_clipboard_err_msg": "Failed to grab clipboard image: {err}",
        "doc_attach_err_title": "Attachment Error",
        "doc_attach_err_msg": "Could not load image: {err}",
    },

    "id": {
        # App Window & Header
        "app_title": "Crazy Doctor for The Sims 4 (Edisi macOS) - WeduGames",
        "header_brand_title": "⚡ CRAZY DOCTOR",
        "header_brand_subtitle": " FOR THE SIMS 4 (MAC)",
        "engine_core_online": "Crazy Core: Siaga",
        "engine_core_offline": "Crazy Core: Standby",
        "btn_change_folder": "Ganti Folder",
        "folder_not_found": "Folder Tidak Ditemukan",
        "lang_toggle_btn": "🌐 🇮🇩 ID | EN",
        "lang_btn_text": "🌐 🇮🇩 ID",
        "folder_dialog_title": "Pilih Folder Pengguna The Sims 4 (berisi Mods, saves, Options.ini)",
        "folder_updated_title": "Folder Diperbarui",
        "folder_updated_msg": "Berhasil mengatur folder The Sims 4 ke:\n{path}",

        # Sidebar Navigation
        "nav_main_heading": "NAVIGASI UTAMA",
        "nav_dashboard": "📊  Dasbor",
        "nav_doctor_core": "🩺  Dokter WeduGames",
        "nav_doctor": "🩺  Dokter & Skrip",
        "nav_graphics": "🎮  Metal & Grafis",
        "nav_mods": "👗  Mod & CC 3D",
        "nav_saves": "💾  Save & Tray",
        "nav_system": "⚙️  Sistem macOS & VIP",
        "vip_badge_title": "EDISI PRO MACOS",
        "vip_badge_version": "v1.0.0 Universal2\nWeduGames Engine",

        # Dashboard Tab
        "dash_score_title": "SKOR KESEHATAN",
        "dash_status_healthy": "SEHAT OPTIMAL",
        "dash_status_warning": "PERINGATAN KUNING",
        "dash_status_critical": "KRITIS MERAH",
        "dash_title": "DOKTER SISTEM ALL-IN-ONE THE SIMS 4 MACOS",
        "dash_desc": "Diagnostik Otonom, Pengoptimal Metal VRAM & Perbaikan Otomatis Karantina Aman.",
        "dash_last_scan_never": "Pemindaian Terakhir: Belum Pernah",
        "dash_last_scan_time": "Pemindaian Terakhir: {time}",
        "dash_btn_scan": "⚡ 1-KLIK PINDAI PENUH",
        "dash_btn_scanning": "MEMINDAI...",
        "dash_btn_autofix": "🛠️ PERBAIKI SEMUA OTOMATIS",
        "dash_btn_fixing": "MEMPERBAIKI...",
        "dash_card_crit_title": "MASALAH KRITIS",
        "dash_card_crit_desc": "Crash, mod rusak 0-byte, kedalaman skrip bermasalah, ghost iCloud",
        "dash_card_warn_title": "PERINGATAN & SUMBER LAG",
        "dash_card_warn_desc": "Mesh 3D kebesaran, mesh induk hilang, tumpukan cache Metal",
        "dash_card_healthy_title": "SISTEM SEHAT",
        "dash_card_healthy_desc": "File Options.ini, save game aktif, konfigurasi Metal, izin macOS",
        "dash_card_healthy_optimal": "OPTIMAL",
        "dash_log_title": "🔍 LOG DIAGNOSTIK & TEMUAN AKTIF",
        "dash_issues_count": "{count} Masalah Ditemukan",
        "dash_issues_detected": "{count} Masalah Terdeteksi",
        "dash_empty_state": "✨ Belum ada pemindaian yang dijalankan. Klik '1-KLIK PINDAI PENUH' di atas untuk memulai.",
        "dash_all_clean": "🎉 Selamat! Instalasi The Sims 4 macOS Anda 100% bersih, optimal, dan sehat!",
        "dash_autofixable_tag": "BISA DIPERBAIKI OTOMATIS ✓",
        "dash_dialog_scan_error_title": "Kesalahan Pemindaian",
        "dash_dialog_scan_error_msg": "Terjadi kesalahan saat pemindaian: {error}",
        "dash_dialog_autofix_title": "Perbaiki Semua Otomatis",
        "dash_dialog_autofix_confirm": "Perbaikan Otomatis akan menjalankan perbaikan sistematis (ratakan skrip dalam, bersihkan cache Metal, pulihkan file ghost iCloud, batasi FPS MacBook, matikan proses zombie, dan amankan save file).\n\nBackup karantina aman akan dibuat di 'Quarantine_WeduGames'. Lanjutkan?",
        "dash_dialog_autofix_done_title": "Perbaikan Otomatis Selesai!",
        "dash_dialog_autofix_done_msg": "Perbaikan berhasil diselesaikan!\n\nSkor Kesehatan: {initial_score} ➔ {new_score} ({new_status})\nTindakan Dijalankan ({actions_count}):{actions_str}\n\nLokasi Backup:\n{quarantine_dir}",
        "dash_dialog_autofix_err_title": "Kesalahan Perbaikan Otomatis",
        "dash_dialog_autofix_err_msg": "Perbaikan Otomatis mengalami kesalahan: {error}",

        # Doctor Tab
        "doc_sec_script_title": "📜 PENYELARAS KEDALAMAN MOD SKRIP",
        "doc_btn_flatten": "⚡ Ratakan Semua Skrip Terlalu Dalam",
        "doc_script_desc": "Sims 4 tidak bisa memuat file .ts4script yang ditaruh 2 subfolder atau lebih dalam. Pindahkan aman ke Kedalaman 1.",
        "doc_script_status_default": "Sims 4 tidak bisa memuat file .ts4script yang ditaruh 2 subfolder atau lebih dalam. Pindahkan aman ke Kedalaman 1.",
        "doc_script_status_done": "✓ Tindakan Terakhir: Meratakan {count} mod skrip ke Kedalaman 1. Game sekarang dapat mengenalinya!",
        "doc_sec_crash_title": "💥 PENGURAI LASTEXCEPTION & CRASH",
        "doc_btn_analyze_crash": "🔎 Analisis Log Terbaru",
        "doc_crash_placeholder": "Klik 'Analisis Log Terbaru' untuk membaca dan mencocokkan stack trace dengan mod penyebab...",
        "doc_sec_corrupt_title": "🗑️ PENGISOLASI MOD RUSAK & 0-BYTE",
        "doc_btn_isolate": "🛡️ Karantina Mod Rusak",
        "doc_corrupt_desc": "Mendeteksi file .package 0-byte, unduhan terputus, dan memindahkannya ke Quarantine_WeduGames dengan aman.",
        "doc_corrupt_status_default": "Mendeteksi file .package 0-byte, unduhan terputus, dan memindahkannya ke Quarantine_WeduGames dengan aman.",
        "doc_corrupt_status_done": "✓ Tindakan Terakhir: Mengarantina {count} package rusak.",
        "doc_notice_mods_missing": "Folder Mods tidak ditemukan.",
        "doc_notice_user_missing": "Folder pengguna tidak ditemukan.",
        "doc_flatten_clean": "Semua mod skrip (.ts4script) sudah berada pada kedalaman aman (Kedalaman 0 atau 1).",
        "doc_flatten_success": "Berhasil meratakan {count} mod skrip ke Kedalaman 1!{log_str}",
        "doc_crash_clean": "Tidak ada log lastException atau lastCrash di folder game. Game Anda bersih!",
        "doc_corrupt_clean": "Tidak ditemukan file package 0-byte atau rusak di folder Mods Anda.",
        "doc_corrupt_success": "Berhasil mengarantina {count} package 0-byte rusak ke:\n{dir}",

        # Graphics & GPU Tab (Metal API)
        "gfx_sec_dx_title": "⚡ APPLE METAL GRAPHICS ENGINE (MACOS)",
        "gfx_dx_current": "Renderer Aktif: {mode}",
        "gfx_dx_checking": "Renderer Aktif: Memeriksa...",
        "gfx_dx_desc": "Apple Metal API memberikan akselerasi grafis native berdaya tinggi, efisiensi termal optimal, dan hemat baterai pada macOS.",
        "gfx_btn_dx11": "Metal Renderer Aktif (macOS Native)",
        "gfx_btn_dx9": "Mode Kompatibilitas",
        "gfx_sec_cache_title": "🧹 PEMBERSIH SHADER METAL & CACHE THUMBNAIL",
        "gfx_btn_purge": "⚡ 1-Klik Bersihkan Cache Metal",
        "gfx_cache_inspecting": "Memeriksa cache Metal...",
        "gfx_cache_summary": "Akumulasi Cache: {size} ({count} file/direktori)",
        "gfx_cache_desc": "Membersihkan localthumbcache dan cache shader Metal native (~/Library/Caches/com.ea.TheSims4/) mengatasi glitch warna pink dan stuttering.",
        "gfx_sec_fps_title": "❄️ PEMBATAS SUHU MACBOOK (60Hz / 120Hz ProMotion)",
        "gfx_fps_desc": "Menu dan loading screen Sims 4 berjalan tanpa batas FPS (500+ FPS), memicu panas tinggi dan suara kipas kencang pada MacBook. Batasi FPS untuk menjaga hardware:",
        "gfx_btn_cap_fps": "Kunci di {fps} FPS",
        "gfx_fps_status_active": "✓ Perlindungan Suhu MacBook Aktif: Framerate dibatasi pada {limit}",
        "gfx_fps_status_uncapped": "⚠️ Framerate tidak dibatasi. MacBook berisiko overheat saat loading screen.",
        "gfx_cache_purged_title": "Cache Metal Dibersihkan",
        "gfx_cache_purged_msg": "Berhasil membersihkan {count} item cache!\nMembebaskan {size} ruang penyimpanan.",

        # Mods & 3D CC Tab
        "mods_sec_mesh_title": "📐 PROFILER MESH 3D & DETEKTOR SUMBER LAG",
        "mods_btn_mesh_scan": "🔍 Pindai Mesh CC",
        "mods_mesh_desc": "Memindai mesh GEOM untuk polycount ekstrem (>30rb poligon) dan mesh induk yang hilang.",
        "mods_mesh_placeholder": "Klik 'Pindai Mesh CC' untuk memeriksa geometri 3D...",
        "mods_mesh_scanning": "Memindai file package...",
        "mods_mesh_scanning_bg": "Memprofil mesh 3D di latar belakang...",
        "mods_mesh_complete": "Pemindaian selesai: {lag_bombs} lag bomb, {orphans} recolor tanpa mesh induk.",
        "mods_sec_townie_title": "👗 PEMBERSIH CC NPC TOWNIE (AllowForRandom = 0)",
        "mods_btn_townie": "🚫 Bersihkan Semua CC Townie",
        "mods_btn_townie_running": "MEMBERSIHKAN...",
        "mods_townie_desc": "Mencegah NPC townie acak memakai rambut mod heboh, aksesoris nyeleneh, atau pakaian alpha rusak.",
        "mods_townie_status_done": "✓ Membersihkan {pkgs} package ({casps} bagian CAS).",
        "mods_townie_confirm_title": "Pembersih CC Townie",
        "mods_townie_confirm_msg": "Ini akan memindai package CAS dan mematikan AllowForRandom (agar townie tidak memakai CC aneh).\n\nAnda tetap bisa memilih dan memakai item ini untuk Sim Anda di CAS seperti biasa. Lanjutkan?",
        "mods_townie_done_title": "Pembersih Townie Selesai",
        "mods_townie_done_msg": "Berhasil membersihkan {pkgs} package dan menonaktifkan {casps} flag AllowForRandom!\nNPC townie tidak akan lagi muncul memakai item ini.",
        "mods_sec_tex_title": "🖼️ PENGOPTIMAL TEKSTUR (Lanczos Downsampler)",
        "mods_btn_opt_tex": "⚡ Optimalkan Tekstur 4K ke 2K",
        "mods_tex_desc": "Tekstur 4096x4096 (4K) tanpa kompresi membebani memori terpadu (Unified Memory) macOS. Turunkan ke 2K tajam dengan resampling Lanczos.",
        "mods_tex_status_done": "✓ Mengoptimalkan {count} tekstur, menghemat {freed}.",
        "mods_tex_confirm_title": "Pengurang Ukuran Tekstur",
        "mods_tex_confirm_msg": "Menurunkan tekstur CC 4K/8K ke 2K Lanczos menghemat pemakaian memori grafis macOS hingga 60%.\nProses ini mempertahankan kualitas visual tajam sekaligus menghilangkan patah-patah/stutter. Lanjutkan?",
        "mods_tex_done_title": "Optimalisasi Tekstur Selesai",
        "mods_tex_done_msg": "Berhasil mengoptimalkan {count} tekstur ke 2K Lanczos!\nMenghemat {freed} penyimpanan dan meringankan beban grafis.",
        "mods_sec_5050_title": "⚖️ OTOMASI PENCARIAN 50/50 (METODE BINARY SEARCH)",
        "mods_5050_step_inactive": "Langkah 0: Tidak Aktif",
        "mods_5050_step_progress": "Langkah {step}: Menguji {active} mod ({suspects} tersisa)",
        "mods_5050_step_isolated": "PENYEBAB DITEMUKAN!",
        "mods_5050_desc_default": "Lacak penyebab crash atau bug UI misterius dengan membagi mod menjadi dua bagian secara sistematis hingga mod penyebab ditemukan.",
        "mods_5050_desc_progress": "Sesi 50/50 sedang berjalan! Separuh mod aktif dalam game, separuh lagi dipisahkan. Uji game sekarang lalu klik tombol di bawah:",
        "mods_5050_desc_isolated": "🎯 Mod penyebab berhasil ditemukan:\n{mod}",
        "mods_btn_5050_start": "Mulai Sesi 50/50 Baru",
        "mods_btn_5050_broken": "❌ Error Masih Ada",
        "mods_btn_5050_clean": "✅ Game Berjalan Normal",
        "mods_btn_5050_cancel": "Pulihkan Semua & Batal",

        # Saves & Tray Tab
        "saves_sec_saves_title": "💾 PENGARSIP SAVE GAME & ROLLBACK 1-KLIK",
        "saves_btn_snapshot": "📸 Buat Snapshot",
        "saves_btn_purge_ver": "🧹 Bersihkan File Backup .ver Lama",
        "saves_sec_tray_title": "📦 PERPUSTAKAAN TRAY & PEMERIKSA CC",
        "saves_btn_scan_tray": "🔍 Pindai Library Tray",
        "saves_btn_export_bundle": "📦 Ekspor Paket CC (.zip)",
        "saves_tray_desc": "Memeriksa Household dan Lot di folder Tray untuk mendeteksi CC hilang (Sim botak atau tembok hilang).",
        "saves_tray_placeholder": "Klik 'Pindai Library Tray' untuk menganalisis Sim dan Lot yang tersimpan...",
        "saves_tray_scanning": "Memindai item Library dan mengindeks file Mods...",
        "saves_tray_status_done": "✓ Berhasil memindai {count} item library.",
        "saves_btn_rollback": "↺ Rollback ke .ver0",
        "saves_status_corrupted": "RUSAK",
        "saves_status_healthy": "SEHAT",
        "saves_not_found": "Folder Saves tidak ditemukan.",
        "saves_no_slots": "Tidak ditemukan file save di folder saves/.",
        "saves_slot_label": "Slot {dec} ({hex})",
        "saves_slot_autosave": " [AUTOSAVE]",
        "saves_slot_details": "Ukuran: {size} | Terakhir Dimainkan: {last_played} | Backup: {ver_count} versi (.ver0-.ver4)",
        "saves_rollback_confirm_title": "Konfirmasi Rollback",
        "saves_rollback_confirm_msg": "Yakin ingin me-rollback Slot {slot} ke .ver0?\n\nCheckpoint pengaman otomatis dari save saat ini akan dibuat sebelum pemulihan.",
        "saves_rollback_done_title": "Rollback Selesai",
        "saves_rollback_err_title": "Rollback Gagal",
        "saves_snapshot_prompt_title": "Buat Snapshot",
        "saves_snapshot_prompt_msg": "Masukkan nama/label untuk checkpoint save game ini:",
        "saves_snapshot_done_title": "Snapshot Berhasil Dibuat",
        "saves_snapshot_done_msg": "Berhasil membuat checkpoint:\n{msg}",
        "saves_snapshot_err_title": "Snapshot Gagal",
        "saves_purge_confirm_title": "Hapus Backup Lama",
        "saves_purge_confirm_msg": "Ini akan menghapus file backup berputar yang lebih lama (.ver1 - .ver4), namun TETAP MEMPERTAHANKAN .ver0 sebagai backup darurat.\n\nLanjutkan untuk menghemat ruang disk?",
        "saves_purge_done_title": "Pembersihan Selesai",
        "saves_purge_done_msg": "Menghapus {deleted} file backup lama.\nMembebaskan {freed} ruang penyimpanan!",

        # System & VIP Tab (macOS)
        "sys_sec_ghost_title": "☁️ PEMULIH FILE GHOST ICLOUD DRIVE",
        "sys_btn_hydrate": "⚡ Unduh Paksa Semua File Lokal",
        "sys_ghost_desc": "Fitur 'Optimize Mac Storage' pada iCloud Drive meng-evict mod menjadi file .icloud ghost dan membekukan game. Memaksa semua mod & save terunduh di disk lokal.",
        "sys_ghost_found": "⚠️ Ditemukan {count} file ghost iCloud! Game berisiko freeze saat loading.",
        "sys_ghost_clean": "✓ Semua file di Mods dan saves 100% tersimpan penuh di disk lokal.",
        "sys_sec_split_title": "🔀 PENGGABUNG FOLDER DOKUMEN GANDA",
        "sys_btn_merge": "🔗 Gabungkan Folder Sekunder",
        "sys_split_desc": "Mendeteksi jika iCloud Drive membuat folder 'The Sims 4' kedua di Documents lain, dan menggabungkan file yang tertinggal.",
        "sys_split_detected": "⚠️ Folder ganda terdeteksi di {count} lokasi (misal: Dokumen Lokal & Dokumen iCloud).",
        "sys_split_clean": "✓ Tidak ada folder Dokumen terpisah. Semua data game tersinkronisasi rapi.",
        "sys_sec_zombie_title": "🧟 PEMBASMI PROSES ZOMBIE EA APP & TS4",
        "sys_btn_kill_zombies": "💀 Basmi Semua Proses Zombie",
        "sys_zombie_desc": "Menghentikan layanan EA Desktop dan The Sims 4 macet yang mengunci file package dan membuat game gagal dibuka.",
        "sys_zombie_detected": "⚠️ Ditemukan {count} proses latar belakang aktif: {names}",
        "sys_zombie_clean": "✓ Tidak ada proses gantung di latar belakang. Penguncian file aman.",
        "sys_sec_cfa_title": "🛡️ IZIN MACOS & FULL DISK ACCESS",
        "sys_cfa_checking": "Memeriksa izin akses file macOS...",
        "sys_cfa_desc": "Sistem privasi macOS App Sandbox membutuhkan akses tulis ke ~/Documents/Electronic Arts/The Sims 4 agar game dapat menyimpan data tanpa Error Code 0.",
        "sys_cfa_enabled_ok": "✓ Izin Tulis & Full Disk Access BERJALAN NORMAL.",
        "sys_cfa_enabled_blocked": "⚠️ Izin tulis DIBATASI! Berikan izin 'Full Disk Access' di System Settings > Privacy & Security macOS untuk mencegah Error 0.",
        "sys_cfa_disabled_ok": "✓ Izin tulis folder tidak terhalang.",
        "sys_sec_vip_title": "🚀 REGISTRASI 1-KEY TERPADU & PELUNCUR VIP",
        "sys_btn_launch": "▶️ Mainkan The Sims 4.app",
        "sys_exe_searching": "Mencari bundle The Sims 4.app...",
        "sys_exe_detected": "✓ Terdeteksi: {exe}",
        "sys_exe_not_found": "⚠️ Bundle The Sims 4.app tidak ditemukan otomatis di /Applications.",
        "sys_hydrate_done_title": "Pemulihan Selesai",
        "sys_hydrate_done_msg": "Berhasil memulihkan {success} file cloud ke disk lokal. Gagal: {failed}.",
        "sys_merge_confirm_title": "Konfirmasi Penggabungan",
        "sys_merge_confirm_msg": "Gabungkan file dari folder sekunder:\n{src}\n\nke dalam folder utama aktif:\n{dst}?\n\nFile yang lebih baru tidak akan ditimpa.",
        "sys_merge_done_title": "Penggabungan Selesai",
        "sys_zombie_done_title": "Pembasmi Proses",
        "sys_zombie_done_msg": "Menghentikan {count} proses:{logs}",

        # WeduGames Doctor Tab
        "doc_banner_title": "🩺 DOKTER WEDUGAMES & ASISTEN MULTIMODAL",
        "doc_banner_desc": "Mesin Diagnostik Cerdas Otonom (Crazy Core) • Analisis Screenshot Visual, Drag & Drop & Solusi 1-Klik.",
        "doc_btn_briefing": "🩺 Laporan Dokter WeduGames",
        "doc_key_label": "Kunci Engine:",
        "doc_placeholder_key": "Masukkan kunci atau tempel banyak...",
        "doc_btn_save_key": "➕ Tambah/Simpan",
        "doc_btn_pool": "🔑 Pool ({count}) {arrow}",
        "doc_btn_sync_cloud": "🌐 Sinkron Cloud",
        "doc_model_label": "Model:",
        "doc_pool_title": "🔑 KUMPULAN KUNCI ENGINE (Load Balancing & Failover)",
        "doc_pool_stats": "Kunci Aktif: {count} | Sumber: {source} | Strategi: Round-Robin",
        "doc_pool_paste_label": "📋 Tempel beberapa kunci (satu per baris, pisahkan koma atau spasi):",
        "doc_btn_import_batch": "📥 Impor Semua Kunci ke Pool",
        "doc_btn_clear_input": "🧹 Bersihkan Input",
        "doc_btn_clear_pool": "🗑️ Kosongkan Seluruh Pool",
        "doc_btn_revert_cloud": "🌐 Kembali ke Pool Cloud",
        "doc_btn_close_panel": "✕ Tutup Panel",
        "doc_active_keys_queue": "Kunci Aktif di Pool (Antrean Eksekusi Round-Robin):",
        "doc_action_rec_title": "⚡ TINDAKAN WEDUGAMES DISARANKAN: {label}",
        "doc_btn_execute_now": "⚡ Terapkan Solusi WeduGames",
        "doc_btn_dismiss": "✕ Tutup",
        "doc_btn_attach": "📎 Lampirkan",
        "doc_btn_paste": "📋 Tempel",
        "doc_input_placeholder": "Jelaskan masalah, kode error, atau tanya solusi... (Tekan Enter untuk Kirim)",
        "doc_btn_send": "Kirim 🚀",
        "doc_btn_thinking": "Menganalisis...",
        "doc_btn_assessing": "Memeriksa...",
        "doc_badge_doctor": "🩺 Dokter WeduGames",
        "doc_badge_player": "👤 Pemain",
        "doc_welcome_text": (
            "👋 **Halo! Saya Dokter WeduGames & Spesialis Sistem The Sims 4 untuk macOS.**\n\n"
            "Ada yang bisa saya bantu untuk mengembalikan game Anda ke kondisi prima hari ini?\n"
            "• **Glitch Visual**: Lampirkan screenshot Error 102/109, tanda tanya merah-putih pada Sim, shader Metal pink, atau Sim melar.\n"
            "• **Deskripsi Masalah**: Ceritakan masalah game macet, loading tiada henti, atau error saat save.\n"
            "• **Perbaikan Otomatis**: Jika penyebabnya diketahui, saya akan berikan **Solusi 1-Klik** yang bisa Anda jalankan langsung!\n\n"
            "_💡 Tips: Lampirkan screenshot via tombol **Lampirkan**, **Drag & Drop** file ke tab ini, atau tekan **Cmd+V Tempel** dari clipboard._"
        ),
        "doc_status_cloud": "🌐 Pool Cloud: {count} Kunci Aktif ({count} Keys Active - WeduGames VIP)",
        "doc_status_custom": "👤 Kunci Kustom: {count} Kunci Aktif ({count} Keys Active)",
        "doc_status_balanced": "🟢 {count} Kunci Aktif ({count} Keys Active)",
        "doc_status_single": "🟢 1 Kunci Aktif (Crazy Core)",
        "doc_status_offline": "🟡 Mode Heuristik Offline (0 Keys / Kunci)",
        "doc_status_online_badge": "● Dokter WeduGames Aktif",
        "doc_status_offline_badge": "● Dokter WeduGames Offline (Mode Heuristik)",
        "doc_status_badge_tooltip": "Jaringan Neural Cloud Otonom Terhubung (WeduGames VIP Zero-Setup)",

        # Common
        "common_notice": "Pemberitahuan",
        "common_error": "Kesalahan",
        "common_success": "Berhasil",
        "common_none": "Tidak ada.",
        "common_warning": "Peringatan",

        # Doctor Tab Dialogs
        "doc_dialog_script_title": "Dokter Skrip",
        "doc_dialog_isolate_title": "Pengisolasi Mod",
        "doc_dialog_isolate_done_title": "Isolasi Selesai",
        "doc_crash_log_file": "FILE LOG: {file}",
        "doc_crash_summary": "RINGKASAN: {summary}",
        "doc_crash_culprits": "MOD PENYEBAB TERDETEKSI:",
        "doc_crash_culprit_item": " • Mod: {mod} (Pembuat: {author}) - Tingkat: {sev}\n   Saran: {advice}",
        "doc_crash_engine_err": "ERROR ENGINE: {err}",
        "doc_crash_traceback": "PRATINJAU TRACEBACK:",

        # Graphics Tab Dialogs
        "gfx_dialog_dx_title": "Apple Metal Graphics Engine",
        "gfx_dialog_dx_success": "Berhasil mengonfigurasi Apple Metal untuk {mode}!",
        "gfx_dialog_dx_error": "Gagal mengonfigurasi Metal: {error}",
        "gfx_dialog_fps_title": "Pembatas Suhu MacBook",
        "gfx_dialog_fps_success": "Batas framerate {fps} FPS berhasil diterapkan! Perlindungan suhu aktif.",
        "gfx_dialog_fps_error": "Gagal menerapkan batas FPS: {error}",

        # Mods Tab Dialogs
        "mods_mesh_res_header": "Hasil Analisis Mesh 3D:\n",
        "mods_mesh_res_summary": "Memindai {pkg_count} file package ({mesh_count} mesh GEOM):\n",
        "mods_mesh_res_lag_bombs": "⚠️ SUMBER LAG POLYCOUNT TINGGI (>30.000 segitiga):",
        "mods_mesh_res_orphans": "⚠️ RECOLOR TANPA INDUK (Base mesh hilang di folder Mods/):",
        "mods_mesh_res_clean": "✓ Semua mesh 3D yang dipindai normal dan memiliki mesh induk yang valid.",
        "mods_5050_dialog_title": "Otomasi 50/50",

        # Saves & Tray Tab Dialogs
        "saves_tray_none_found": "Tidak ditemukan file (.trayitem) di folder Tray/ Anda.",
        "saves_tray_scanned_header": "Berhasil memindai {count} Item Library dari folder Tray/:\n",
        "saves_tray_creator": "  Pembuat: {creator}",
        "saves_tray_found_cc": "  Package CC Ditemukan: {count}",
        "saves_tray_missing_cc": "  ⚠️ Item CC Hilang: {count} (Sim/Lot bisa botak atau kosong)",
        "saves_export_bundle_title": "Ekspor Paket CC",
        "saves_export_bundle_first_scan": "Silakan klik 'Pindai Library Tray' terlebih dahulu untuk mengindeks item Anda.",
        "saves_export_bundle_dialog_title": "Ekspor Paket CC untuk '{name}'",
        "saves_export_bundle_done_title": "Ekspor Selesai",
        "saves_export_bundle_done_msg": "Berhasil mengekspor '{name}' dan semua package CC terkait ke:\n{path}",
        "saves_export_bundle_err_title": "Ekspor Gagal",
        "saves_export_bundle_err_msg": "Gagal mengekspor file arsip CC bundle.",

        # System Tab Dialogs
        "sys_cfa_non_windows": "Sistem operasi macOS.",
        "sys_dialog_select_exe_title": "Pilih File The Sims 4.app",
        "sys_game_launched_title": "Game Dimainkan",
        "sys_game_launched_msg": "Menjalankan The Sims 4:\n{exe}",
        "sys_launch_err_title": "Gagal Menjalankan Game",
        "sys_launch_err_msg": "Gagal memainkan game: {err}",
        "sys_merge_none_found": "Tidak ditemukan folder Dokumen yang terbagi.",
        "sys_merge_no_secondary": "Folder sekunder tidak teridentifikasi.",

        # WeduGames Doctor Tab Dialogs & Extras
        "doc_btn_remove_attach": "✕ Hapus",
        "doc_chat_request_briefing_scan": "Tolong jalankan pemindaian dan buatkan Laporan Dokter WeduGames tentang kesehatan Sims 4 saya.",
        "doc_chat_doctor_assessing": "Memulai pemeriksaan kesehatan dan menyusun Laporan Dokter WeduGames...",
        "doc_chat_request_briefing": "Buatkan Laporan Dokter WeduGames berdasarkan hasil pemindaian terbaru saya.",
        "doc_chat_screenshot_submitted": "[Screenshot dikirim untuk diagnosis]",
        "doc_btn_executing_action": "Menjalankan Solusi...",
        "doc_action_executed_success": "✅ **Solusi Berhasil Dijalankan [{label}]:**\n\n{msg}",
        "doc_action_executed_failed": "❌ **Solusi Gagal Dijalankan [{label}]:**\n\n{msg}",
        "doc_action_done_title": "Solusi WeduGames Selesai",
        "doc_action_err_title": "Eksekusi Gagal",
        "doc_key_dialog_title": "Mesin Crazy Core",
        "doc_key_err_min_length": "Kunci API harus lebih panjang dari 10 karakter.",
        "doc_key_err_enter_valid": "Harap masukkan kunci API yang valid.",
        "doc_key_saved_msg": "Kunci API kustom aktif dan siap digunakan!\nKunci: {key}",
        "doc_key_config_updated": "Konfigurasi engine diperbarui.\nKunci Aktif: {count}",
        "doc_batch_title": "Impor Kunci Sekaligus",
        "doc_batch_paste_first": "Harap tempel satu atau beberapa kunci API ke kotak teks.",
        "doc_batch_none_valid": "Tidak ditemukan kunci yang valid. Setiap kunci harus lebih dari 10 karakter.",
        "doc_clear_pool_title": "Konfirmasi Kosongkan Pool",
        "doc_clear_pool_confirm": "Apakah Anda yakin ingin menghapus SEMUA kunci API dari pool?",
        "doc_copied_title": "Disalin",
        "doc_copied_msg": "Kunci API berhasil disalin ke clipboard.",
        "doc_cloud_sync_title": "Sinkronisasi Cloud",
        "doc_cloud_sync_success": "Kunci cloud berhasil disinkronkan!\nJumlah Kunci Aktif: {count}",
        "doc_cloud_pool_restored_title": "Pool Cloud Dipulihkan",
        "doc_clipboard_title": "Papan Klip",
        "doc_clipboard_none_found": "Tidak ditemukan gambar di clipboard.",
        "doc_clipboard_err_title": "Kesalahan Clipboard",
        "doc_clipboard_err_msg": "Gagal mengambil gambar dari clipboard: {err}",
        "doc_attach_err_title": "Kesalahan Lampiran",
        "doc_attach_err_msg": "Tidak dapat memuat gambar: {err}",
    }
}


class I18nManager:
    """Manages bilingual UI strings, persistence in doctor_config.json, and live listeners."""

    _instance: Optional["I18nManager"] = None

    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path or self._resolve_config_path()
        self._listeners: List[Callable[[str], None]] = []
        self._current_language = self._load_persisted_language()

    @classmethod
    def get_instance(cls) -> "I18nManager":
        if cls._instance is None:
            cls._instance = I18nManager()
        return cls._instance

    @staticmethod
    def _resolve_config_path() -> str:
        """Finds or resolves the preferred location for doctor_config.json on macOS."""
        home = os.path.expanduser("~")
        if sys.platform == "darwin":
            mac_cfg = os.path.join(home, "Library", "Application Support", "WeduGames", "TheSims4Doctor", "doctor_config.json")
            if os.path.isfile(mac_cfg):
                return mac_cfg

        # Next to executable if frozen (.app bundle Contents/MacOS or onefile)
        if getattr(sys, "frozen", False):
            exe_dir = os.path.dirname(sys.executable)
            exe_cfg = os.path.join(exe_dir, "doctor_config.json")
            if os.path.isfile(exe_cfg):
                return exe_cfg
            if sys.platform == "darwin":
                return mac_cfg

        # Development mode: project root
        proj_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        cfg_root = os.path.join(proj_root, "doctor_config.json")
        return cfg_root

    def _load_persisted_language(self) -> str:
        """Reads language from doctor_config.json or falls back to DEFAULT_LANGUAGE ('id')."""
        try:
            if os.path.isfile(self.config_path):
                with open(self.config_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    lang = data.get("language")
                    if lang in SUPPORTED_LANGUAGES:
                        return lang
        except Exception:
            pass
        return DEFAULT_LANGUAGE

    def save_persisted_language(self, lang: str) -> bool:
        """Saves selected language into doctor_config.json."""
        if lang not in SUPPORTED_LANGUAGES:
            return False

        def _write_to(target_path: str) -> bool:
            data = {}
            if os.path.isfile(target_path):
                try:
                    with open(target_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                except Exception:
                    data = {}
            data["language"] = lang
            os.makedirs(os.path.dirname(os.path.abspath(target_path)), exist_ok=True)
            with open(target_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)
            self.config_path = target_path
            return True

        try:
            return _write_to(self.config_path)
        except Exception:
            try:
                home = os.path.expanduser("~")
                fallback_p = os.path.join(home, "Library", "Application Support", "WeduGames", "TheSims4Doctor", "doctor_config.json")
                return _write_to(fallback_p)
            except Exception:
                return False

    def get_language(self) -> str:
        return self._current_language

    def set_language(self, lang: str) -> bool:
        if lang not in SUPPORTED_LANGUAGES:
            raise ValueError(f"Unsupported language '{lang}'. Supported: {SUPPORTED_LANGUAGES}")
        if self._current_language == lang:
            return True
        self._current_language = lang
        self.save_persisted_language(lang)
        self.notify_listeners()
        return True

    def toggle_language(self) -> str:
        new_lang = "en" if self._current_language == "id" else "id"
        self.set_language(new_lang)
        return new_lang

    def register_listener(self, callback: Callable[[str], None]):
        if callback not in self._listeners:
            self._listeners.append(callback)

    def unregister_listener(self, callback: Callable[[str], None]):
        if callback in self._listeners:
            self._listeners.remove(callback)

    def notify_listeners(self):
        for cb in list(self._listeners):
            try:
                cb(self._current_language)
            except Exception:
                pass

    def translate(self, key: str, default: Optional[str] = None, **kwargs) -> str:
        lang_dict = TRANSLATIONS.get(self._current_language, TRANSLATIONS.get("en", {}))
        text = lang_dict.get(key)
        if text is None:
            text = TRANSLATIONS.get("en", {}).get(key, default or key)
        if kwargs and isinstance(text, str):
            try:
                return text.format(**kwargs)
            except Exception:
                return text
        return text


# Module-level convenience singletons
i18n = I18nManager.get_instance()
t = i18n.translate
set_language = i18n.set_language
get_language = i18n.get_language
toggle_language = i18n.toggle_language
