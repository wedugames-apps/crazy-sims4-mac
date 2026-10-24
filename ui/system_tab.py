"""
==============================================================================
Crazy Doctor for The Sims 4 (macOS Edition) - System & VIP Tab
==============================================================================
Native macOS Environment, Permission & License Management:
- iCloud Drive Ghost File Hydrator (Evicted .icloud packages)
- Split Documents Folder Merger (Local ~/Documents vs iCloud Drive)
- macOS EA Desktop & TS4 Process Killer & File Unlocker
- macOS Full Disk Access & App Sandbox Privacy Diagnostics
- Unified 1-Key macOS Registration System & Auto-Unlock Status
"""

import os
import sys
from tkinter import messagebox
import customtkinter as ctk

from ui.theme import (
    BG_CARD, BORDER_COLOR, NEON_CYAN, NEON_CYAN_LIGHT, ELECTRIC_BLUE,
    COLOR_HEALTHY, COLOR_WARNING, COLOR_CRITICAL, PURPLE_ACCENT,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, get_font, neon_btn
)
from diagnostics.health_suite import MasterHealthSuite
from diagnostics.ea_killer import ProcessKiller
from core.system import SystemIntegration
from core.license import MacLicenseManager
from core.i18n import t


class SystemTab(ctk.CTkFrame):
    """Deep macOS system, iCloud Drive, permissions, and 1-Key License manager."""

    def __init__(self, master, health_suite: MasterHealthSuite):
        super().__init__(master, fg_color="transparent")
        self.health_suite = health_suite
        self._build_ui()
        self.refresh_system_status()

    def _build_ui(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=15)

        # 1. Unified 1-Key macOS Registration & VIP Suite Section
        sec_lic = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=12, border_width=1.5, border_color="#3B82F6")
        sec_lic.pack(fill="x", pady=(0, 15))

        lic_head = ctk.CTkFrame(sec_lic, fg_color="transparent")
        lic_head.pack(fill="x", padx=20, pady=(15, 8))

        self.lbl_sec_lic = ctk.CTkLabel(
            lic_head, text=t("sys_sec_vip_title"),
            font=get_font(14, "bold"), text_color=NEON_CYAN
        )
        self.lbl_sec_lic.pack(side="left")

        self.lbl_lic_badge = ctk.CTkLabel(
            lic_head, text="Checking VIP...",
            font=get_font(11, "bold"), text_color=COLOR_HEALTHY
        )
        self.lbl_lic_badge.pack(side="right")

        self.lbl_lic_desc = ctk.CTkLabel(
            sec_lic,
            text=(
                "Unified 1-Key macOS System: If you activated EA Server Dashboard for Mac, "
                "Crazy Doctor auto-unlocks instantly. Accepts WG-TS4M-XXXX-XXXX license keys, "
                "validates via Cloudflare R2, and binds native macOS Hardware UUID."
            ),
            font=get_font(11), text_color=TEXT_SECONDARY, wraplength=760, justify="left"
        )
        self.lbl_lic_desc.pack(anchor="w", padx=20, pady=(0, 10))

        # License status and key input box
        lic_input_row = ctk.CTkFrame(sec_lic, fg_color="transparent")
        lic_input_row.pack(fill="x", padx=20, pady=(0, 15))

        self.entry_key = ctk.CTkEntry(
            lic_input_row,
            placeholder_text="Enter WG-TS4M-XXXX-XXXX License Key...",
            font=get_font(12),
            height=34,
            width=360,
            border_color="#2A3B58",
            fg_color="#0A0E17",
            text_color=TEXT_PRIMARY
        )
        self.entry_key.pack(side="left", padx=(0, 10))

        self.btn_activate_key = neon_btn(
            lic_input_row, text="🔑 Activate License",
            command=self.activate_key,
            style="cyan", width=150, height=34
        )
        self.btn_activate_key.pack(side="left", padx=(0, 10))

        self.btn_check_unlock = neon_btn(
            lic_input_row, text="⚡ Auto-Detect Cache",
            command=self.auto_detect_license,
            style="purple", width=160, height=34
        )
        self.btn_check_unlock.pack(side="left")

        # 2. iCloud Drive Ghost Hydrator Section
        sec_ghost = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        sec_ghost.pack(fill="x", pady=(0, 15))

        g_head = ctk.CTkFrame(sec_ghost, fg_color="transparent")
        g_head.pack(fill="x", padx=20, pady=(15, 10))

        self.lbl_sec_ghost = ctk.CTkLabel(
            g_head, text=t("sys_sec_ghost_title"),
            font=get_font(14, "bold"), text_color=NEON_CYAN
        )
        self.lbl_sec_ghost.pack(side="left")

        self.btn_hydrate = neon_btn(
            g_head, text=t("sys_btn_hydrate"),
            command=self.run_hydration,
            style="cyan", width=220, height=32
        )
        self.btn_hydrate.pack(side="right")

        self.lbl_ghost_desc = ctk.CTkLabel(
            sec_ghost,
            text=t("sys_ghost_desc"),
            font=get_font(11), text_color=TEXT_SECONDARY, wraplength=760, justify="left"
        )
        self.lbl_ghost_desc.pack(anchor="w", padx=20, pady=(0, 4))

        self.lbl_ghost_status = ctk.CTkLabel(
            sec_ghost, text="",
            font=get_font(11), text_color=TEXT_SECONDARY
        )
        self.lbl_ghost_status.pack(anchor="w", padx=20, pady=(0, 15))

        # 3. Split Documents Merger Section
        sec_split = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        sec_split.pack(fill="x", pady=(0, 15))

        sp_head = ctk.CTkFrame(sec_split, fg_color="transparent")
        sp_head.pack(fill="x", padx=20, pady=(15, 10))

        self.lbl_sec_split = ctk.CTkLabel(
            sp_head, text=t("sys_sec_split_title"),
            font=get_font(14, "bold"), text_color=COLOR_WARNING
        )
        self.lbl_sec_split.pack(side="left")

        self.btn_merge = neon_btn(
            sp_head, text=t("sys_btn_merge"),
            command=self.run_split_merge,
            style="amber", width=210, height=32
        )
        self.btn_merge.pack(side="right")

        self.lbl_split_desc = ctk.CTkLabel(
            sec_split,
            text=t("sys_split_desc"),
            font=get_font(11), text_color=TEXT_SECONDARY, wraplength=760, justify="left"
        )
        self.lbl_split_desc.pack(anchor="w", padx=20, pady=(0, 4))

        self.lbl_split_status = ctk.CTkLabel(
            sec_split, text="",
            font=get_font(11), text_color=TEXT_SECONDARY
        )
        self.lbl_split_status.pack(anchor="w", padx=20, pady=(0, 15))

        # 4. macOS EA Desktop & TS4 Process Killer Section
        sec_zombie = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        sec_zombie.pack(fill="x", pady=(0, 15))

        z_head = ctk.CTkFrame(sec_zombie, fg_color="transparent")
        z_head.pack(fill="x", padx=20, pady=(15, 10))

        self.lbl_sec_zombie = ctk.CTkLabel(
            z_head, text=t("sys_sec_zombie_title"),
            font=get_font(14, "bold"), text_color=COLOR_CRITICAL
        )
        self.lbl_sec_zombie.pack(side="left")

        self.btn_kill_zombies = neon_btn(
            z_head, text=t("sys_btn_kill_zombies"),
            command=self.run_zombie_killer,
            style="red", width=220, height=32
        )
        self.btn_kill_zombies.pack(side="right")

        self.lbl_zombie_desc = ctk.CTkLabel(
            sec_zombie,
            text=t("sys_zombie_desc"),
            font=get_font(11), text_color=TEXT_SECONDARY, wraplength=760, justify="left"
        )
        self.lbl_zombie_desc.pack(anchor="w", padx=20, pady=(0, 4))

        self.lbl_zombie_status = ctk.CTkLabel(
            sec_zombie, text="",
            font=get_font(11), text_color=TEXT_SECONDARY
        )
        self.lbl_zombie_status.pack(anchor="w", padx=20, pady=(0, 15))

        # 5. macOS Full Disk Access & Privacy Permissions Section
        sec_cfa = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        sec_cfa.pack(fill="x", pady=(0, 15))

        c_head = ctk.CTkFrame(sec_cfa, fg_color="transparent")
        c_head.pack(fill="x", padx=20, pady=(15, 10))

        self.lbl_sec_cfa = ctk.CTkLabel(
            c_head, text=t("sys_sec_cfa_title"),
            font=get_font(14, "bold"), text_color=PURPLE_ACCENT
        )
        self.lbl_sec_cfa.pack(side="left")

        self.lbl_cfa_status = ctk.CTkLabel(
            c_head, text=t("sys_cfa_checking"),
            font=get_font(12, "bold"), text_color=COLOR_HEALTHY
        )
        self.lbl_cfa_status.pack(side="right")

        self.lbl_cfa_desc = ctk.CTkLabel(
            sec_cfa,
            text=t("sys_cfa_desc"),
            font=get_font(11), text_color=TEXT_SECONDARY, wraplength=760, justify="left"
        )
        self.lbl_cfa_desc.pack(anchor="w", padx=20, pady=(0, 15))

        # 6. Game Launcher
        sec_launch = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        sec_launch.pack(fill="x", pady=(0, 10))

        l_head = ctk.CTkFrame(sec_launch, fg_color="transparent")
        l_head.pack(fill="x", padx=20, pady=(15, 10))

        self.lbl_sec_launch = ctk.CTkLabel(
            l_head, text="🚀 THE SIMS 4.APP LAUNCHER",
            font=get_font(14, "bold"), text_color=NEON_CYAN
        )
        self.lbl_sec_launch.pack(side="left")

        self.btn_launch_game = neon_btn(
            l_head, text=t("sys_btn_launch"),
            command=self.launch_sims4,
            style="green", width=220, height=32
        )
        self.btn_launch_game.pack(side="right")

        self.lbl_exe_status = ctk.CTkLabel(
            sec_launch, text=t("sys_exe_searching"),
            font=get_font(11), text_color=TEXT_SECONDARY
        )
        self.lbl_exe_status.pack(anchor="w", padx=20, pady=(0, 15))

    def refresh_system_status(self):
        # 1. License & Auto-Unlock
        unlocked, msg, cache = MacLicenseManager.check_auto_unlock()
        hwid = MacLicenseManager.get_macos_hwid()
        if unlocked:
            key = cache.get("key") or cache.get("license_key") or "VIP-ACTIVE"
            masked = key[:7] + "..." + key[-4:] if len(key) >= 11 else key
            self.lbl_lic_badge.configure(
                text=f"● UNLOCKED ({masked}) [HWID: {hwid[:8]}]",
                text_color="#34D399"
            )
            if hasattr(self, "entry_key") and not self.entry_key.get():
                self.entry_key.insert(0, key)
        else:
            self.lbl_lic_badge.configure(
                text=f"○ Belum Terdaftar [HWID: {hwid[:8]}]",
                text_color=COLOR_WARNING
            )

        # 2. iCloud Ghost Files
        if self.health_suite.cloud_mgr:
            g_info = self.health_suite.cloud_mgr.inspect_ghost_files()
            if g_info["has_ghost_files"]:
                self.lbl_ghost_status.configure(
                    text=t("sys_ghost_found", count=g_info["total_ghosts"]),
                    text_color=COLOR_CRITICAL
                )
            else:
                self.lbl_ghost_status.configure(
                    text=t("sys_ghost_clean"),
                    text_color=COLOR_HEALTHY
                )

        # 3. Split Documents
        split_info = SystemIntegration.detect_split_documents()
        if split_info:
            self.lbl_split_status.configure(
                text=t("sys_split_detected", count=split_info["folder_count"]),
                text_color=COLOR_WARNING
            )
        else:
            self.lbl_split_status.configure(
                text=t("sys_split_clean"),
                text_color=COLOR_HEALTHY
            )

        # 4. Zombies
        zombies = ProcessKiller.list_running_targets()
        if zombies:
            names = ", ".join(z["name"] for z in zombies)
            self.lbl_zombie_status.configure(
                text=t("sys_zombie_detected", count=len(zombies), names=names),
                text_color=COLOR_WARNING
            )
        else:
            self.lbl_zombie_status.configure(
                text=t("sys_zombie_clean"),
                text_color=COLOR_HEALTHY
            )

        # 5. macOS Permissions
        perm_info = SystemIntegration.check_permissions(self.health_suite.ts4_user_folder)
        if perm_info["writable"]:
            self.lbl_cfa_status.configure(
                text=t("sys_cfa_enabled_ok"),
                text_color=COLOR_HEALTHY
            )
        else:
            self.lbl_cfa_status.configure(
                text=t("sys_cfa_enabled_blocked"),
                text_color=COLOR_CRITICAL
            )

        # 6. Binary check
        game_bin = SystemIntegration.find_sims4_game_binary()
        if game_bin:
            self.lbl_exe_status.configure(
                text=t("sys_exe_detected", exe=game_bin),
                text_color=COLOR_HEALTHY
            )
        else:
            self.lbl_exe_status.configure(
                text=t("sys_exe_not_found"),
                text_color=TEXT_MUTED
            )

    def auto_detect_license(self):
        unlocked, msg, cache = MacLicenseManager.check_auto_unlock()
        self.refresh_system_status()
        if unlocked:
            messagebox.showinfo("Auto-Unlock Berhasil", f"🎉 {msg}\nLisensi: {cache.get('key')}")
        else:
            messagebox.showwarning("Auto-Unlock", msg)

    def activate_key(self):
        raw_key = self.entry_key.get().strip()
        if not raw_key:
            messagebox.showwarning("Aktivasi Lisensi", "Silakan masukkan License Key terlebih dahulu.")
            return

        ok, msg, data = MacLicenseManager.activate_license(raw_key)
        self.refresh_system_status()
        if ok:
            messagebox.showinfo("Aktivasi Berhasil", msg)
        else:
            messagebox.showerror("Aktivasi Gagal", msg)

    def run_hydration(self):
        if not self.health_suite.cloud_mgr:
            return
        hydrated, failed = self.health_suite.cloud_mgr.hydrate_all_ghosts()
        self.refresh_system_status()
        messagebox.showinfo(
            t("sys_hydrate_done_title"),
            t("sys_hydrate_done_msg", success=hydrated, failed=failed)
        )

    def run_split_merge(self):
        split_info = SystemIntegration.detect_split_documents()
        if not split_info or len(split_info["folders"]) < 2:
            messagebox.showinfo("Split Merger", t("sys_merge_none_found"))
            return

        primary = self.health_suite.ts4_user_folder
        secondary = [f for f in split_info["folders"] if f != primary]
        if not secondary:
            messagebox.showinfo("Split Merger", t("sys_merge_no_secondary"))
            return

        src_folder = secondary[0]
        if messagebox.askyesno(
            t("sys_merge_confirm_title"),
            t("sys_merge_confirm_msg", src=src_folder, dst=primary)
        ):
            c, msg = SystemIntegration.merge_split_folders(src_folder, primary)
            self.refresh_system_status()
            messagebox.showinfo(t("sys_merge_done_title"), msg)

    def run_zombie_killer(self):
        c, logs = ProcessKiller.kill_all_zombies()
        self.refresh_system_status()
        log_str = "\n" + "\n".join(f" • {l}" for l in logs) if logs else ""
        messagebox.showinfo(
            t("sys_zombie_done_title"),
            t("sys_zombie_done_msg", count=c, logs=log_str)
        )

    def launch_sims4(self):
        game_bin = SystemIntegration.find_sims4_game_binary()
        if not game_bin:
            messagebox.showwarning("Launch Sims 4", t("sys_exe_not_found"))
            return

        try:
            import subprocess
            if sys.platform == "darwin":
                if game_bin.endswith(".app"):
                    subprocess.Popen(["open", game_bin])
                else:
                    subprocess.Popen([game_bin])
            else:
                subprocess.Popen([game_bin])
            messagebox.showinfo(t("sys_game_launched_title"), t("sys_game_launched_msg", exe=game_bin))
        except Exception as e:
            messagebox.showerror(t("sys_launch_err_title"), t("sys_launch_err_msg", err=str(e)))
