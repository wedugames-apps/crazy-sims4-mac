"""
==============================================================================
Crazy Doctor for The Sims 4 (macOS Edition) - Main Application Window
==============================================================================
Modern CustomTkinter desktop interface tailored for macOS featuring:
- Cyberpunk Neon Dark Mode with native Apple typography (SF Pro Text)
- Sidebar navigation with animated pill indicators
- Fluid category tabs (Dashboard, WeduGames Doctor, Graphics & Metal, Mods, Saves, System)
- Unified 1-Key macOS Registration & Auto-Unlock status header
- Dynamic Sims 4 folder selector & native macOS path resolver
"""

import os
import sys
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from PIL import Image, ImageTk

from ui.theme import (
    BG_DARK, BG_SIDEBAR, BG_HEADER, BG_CARD, BORDER_COLOR,
    NEON_CYAN, NEON_CYAN_LIGHT, ELECTRIC_BLUE, COLOR_HEALTHY, COLOR_WARNING,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, get_font, apply_dark_title_bar,
    neon_btn, NEON_BTN_CYAN, NEON_BTN_SECONDARY
)
from diagnostics.health_suite import MasterHealthSuite
from core.license import MacLicenseManager
from ui.dashboard_tab import DashboardTab
from ui.doctor_tab import DoctorTab
from ui.graphics_tab import GraphicsTab
from ui.mods_tab import ModsTab
from ui.saves_tray_tab import SavesTrayTab
from ui.system_tab import SystemTab
from ui.doctor_core_tab import DoctorCoreTab
from core.i18n import i18n, t, toggle_language

try:
    import tkinterdnd2
    DND_AVAILABLE = True
    DND_BASE = tkinterdnd2.TkinterDnD.DnDWrapper
except ImportError:
    DND_AVAILABLE = False
    DND_BASE = object


class AppWindow(ctk.CTk, DND_BASE):
    """Main Application Window for The Sims 4 Crazy Optimizer Suite on macOS."""

    NAV_ITEMS = [
        ("dashboard", "📊  Dashboard"),
        ("doctor_core", "🩺  WeduGames Doctor"),
        ("doctor", "🩺  Doctor & Scripts"),
        ("graphics", "🎮  Metal & Graphics"),
        ("mods", "👗  Mods & 3D CC"),
        ("saves", "💾  Saves & Tray"),
        ("system", "⚙️  macOS System & VIP"),
    ]

    NAV_KEYS = {
        "dashboard": "nav_dashboard",
        "doctor_core": "nav_doctor_core",
        "doctor": "nav_doctor",
        "graphics": "nav_graphics",
        "mods": "nav_mods",
        "saves": "nav_saves",
        "system": "nav_system",
    }

    def __init__(self, ts4_folder=None):
        super().__init__()

        if DND_AVAILABLE:
            try:
                self.TkdndVersion = tkinterdnd2.TkinterDnD._require(self)
            except Exception:
                pass

        self.title(t("app_title"))
        self.geometry("1140x760")
        self.minsize(980, 640)

        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.configure(fg_color=BG_DARK)

        # Center Window on Screen
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        x = max(0, (screen_w - 1140) // 2)
        y = max(0, (screen_h - 760) // 2)
        self.geometry(f"1140x760+{x}+{y}")

        # Dark Title Bar
        apply_dark_title_bar(self)
        self.after(50, lambda: apply_dark_title_bar(self))

        # Window Icon & Branding Assets
        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logo_path = os.path.join(base_dir, "assets", "wedugames_logo.png")
        self.logo_image_header = None
        self.logo_image_sidebar = None
        if os.path.isfile(logo_path):
            try:
                pil_logo = Image.open(logo_path)
                self.logo_image_header = ctk.CTkImage(light_image=pil_logo, dark_image=pil_logo, size=(36, 36))
                self.logo_image_sidebar = ctk.CTkImage(light_image=pil_logo, dark_image=pil_logo, size=(38, 38))
                tk_icon = ImageTk.PhotoImage(pil_logo.resize((32, 32), Image.Resampling.LANCZOS), master=self)
                self.iconphoto(False, tk_icon)
                self._titlebar_icon_ref = tk_icon
            except Exception:
                pass

        # Core Health Suite
        self.health_suite = MasterHealthSuite(ts4_folder)

        self.nav_buttons = {}
        self.tab_frames = {}
        self.active_tab_id = "dashboard"

        # Register i18n listener for instant retranslation
        i18n.register_listener(self.update_ui_language)

        self._build_layout()
        self.switch_tab("dashboard")
        self.check_vip_license_status()

    def _build_layout(self):
        # 1. Top Header Bar
        header = ctk.CTkFrame(self, fg_color=BG_HEADER, height=65, corner_radius=0, border_width=1, border_color=BORDER_COLOR)
        header.pack(fill="x", side="top")
        header.pack_propagate(False)

        # App Brand Title
        brand_box = ctk.CTkFrame(header, fg_color="transparent")
        brand_box.pack(side="left", padx=20, pady=12)

        if self.logo_image_header:
            self.lbl_logo_header = ctk.CTkLabel(brand_box, image=self.logo_image_header, text="")
            self.lbl_logo_header.pack(side="left", padx=(0, 10))

        self.lbl_brand_title = ctk.CTkLabel(
            brand_box, text=t("header_brand_title"),
            font=get_font(16, "bold"), text_color=NEON_CYAN
        )
        self.lbl_brand_title.pack(side="left")

        self.lbl_brand_subtitle = ctk.CTkLabel(
            brand_box, text=t("header_brand_subtitle"),
            font=get_font(15, "bold"), text_color=TEXT_PRIMARY
        )
        self.lbl_brand_subtitle.pack(side="left")

        # VIP Registration Header Badge
        self.lbl_vip_header_badge = ctk.CTkLabel(
            brand_box, text="⚡ Checking...",
            font=get_font(11, "bold"), text_color=COLOR_HEALTHY
        )
        self.lbl_vip_header_badge.pack(side="left", padx=(14, 0))

        # Right Header: Language toggle + Target Folder Box
        right_box = ctk.CTkFrame(header, fg_color="transparent")
        right_box.pack(side="right", padx=20, pady=12)

        # Language Toggle Button
        curr_lang = i18n.get_language()
        lang_text = "🌐 🇮🇩 ID" if curr_lang == "id" else "🌐 🇬🇧 EN"
        self.btn_lang_toggle = neon_btn(
            right_box,
            text=lang_text,
            command=self.on_toggle_language,
            style="secondary",
            width=85,
            height=32,
            font=get_font(11, "bold")
        )
        self.btn_lang_toggle.pack(side="right", padx=(10, 0))

        self.btn_browse_folder = neon_btn(
            right_box,
            text=t("btn_change_folder"),
            command=self.browse_folder,
            style="secondary",
            width=110,
            height=32,
            font=get_font(11)
        )
        self.btn_browse_folder.pack(side="right", padx=(8, 0))

        folder_str = self.health_suite.ts4_user_folder or t("folder_not_found")
        short_folder = folder_str if len(folder_str) < 42 else "..." + folder_str[-38:]
        self.lbl_folder_path = ctk.CTkLabel(
            right_box, text=f"📂 {short_folder}",
            font=get_font(11), text_color=TEXT_SECONDARY
        )
        self.lbl_folder_path.pack(side="right", padx=6)

        # 2. Main Body Container
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True)

        # Sidebar Frame
        sidebar = ctk.CTkFrame(body, fg_color=BG_SIDEBAR, width=225, corner_radius=0, border_width=1, border_color=BORDER_COLOR)
        sidebar.pack(side="left", fill="y")
        sidebar.pack_propagate(False)

        # Navigation Header
        self.lbl_nav_heading = ctk.CTkLabel(
            sidebar, text=t("nav_main_heading"),
            font=get_font(10, "bold"), text_color=TEXT_MUTED
        )
        self.lbl_nav_heading.pack(anchor="w", padx=20, pady=(20, 10))

        # Nav Buttons
        nav_container = ctk.CTkFrame(sidebar, fg_color="transparent")
        nav_container.pack(fill="x", padx=10)

        for tab_id, default_label in self.NAV_ITEMS:
            key = self.NAV_KEYS.get(tab_id)
            label = t(key) if key else default_label
            btn = ctk.CTkButton(
                nav_container,
                text=label,
                font=get_font(12, "bold"),
                anchor="w",
                height=42,
                corner_radius=8,
                fg_color="transparent",
                text_color=TEXT_SECONDARY,
                hover_color="#182338",
                command=lambda tid=tab_id: self.switch_tab(tid)
            )
            btn.pack(fill="x", pady=2)
            self.nav_buttons[tab_id] = btn

        # Sidebar Footer: Brand Badge
        footer_badge = ctk.CTkFrame(sidebar, fg_color="#0F1B2E", corner_radius=8, border_width=1, border_color=BORDER_COLOR)
        footer_badge.pack(side="bottom", fill="x", padx=12, pady=16)

        foot_content = ctk.CTkFrame(footer_badge, fg_color="transparent")
        foot_content.pack(fill="x", padx=10, pady=8)

        if self.logo_image_sidebar:
            self.lbl_logo_sidebar = ctk.CTkLabel(foot_content, image=self.logo_image_sidebar, text="")
            self.lbl_logo_sidebar.pack(side="left", padx=(0, 8))

        foot_text = ctk.CTkFrame(foot_content, fg_color="transparent")
        foot_text.pack(side="left")

        self.lbl_vip_badge_title = ctk.CTkLabel(
            foot_text, text=t("vip_badge_title"),
            font=get_font(10, "bold"), text_color=NEON_CYAN
        )
        self.lbl_vip_badge_title.pack(anchor="w")

        self.lbl_vip_badge_version = ctk.CTkLabel(
            foot_text, text=t("vip_badge_version"),
            font=get_font(9), text_color=TEXT_MUTED, justify="left"
        )
        self.lbl_vip_badge_version.pack(anchor="w")

        # Content Frame
        self.content_frame = ctk.CTkFrame(body, fg_color=BG_DARK, corner_radius=0)
        self.content_frame.pack(side="right", fill="both", expand=True)

        # Pre-instantiate Tabs
        self.tab_frames["dashboard"] = DashboardTab(self.content_frame, self.health_suite)
        self.tab_frames["doctor_core"] = DoctorCoreTab(self.content_frame, self.health_suite)
        self.tab_frames["doctor"] = DoctorTab(self.content_frame, self.health_suite)
        self.tab_frames["graphics"] = GraphicsTab(self.content_frame, self.health_suite)
        self.tab_frames["mods"] = ModsTab(self.content_frame, self.health_suite)
        self.tab_frames["saves"] = SavesTrayTab(self.content_frame, self.health_suite)
        self.tab_frames["system"] = SystemTab(self.content_frame, self.health_suite)

    def check_vip_license_status(self):
        """Auto-detects license cache on macOS and updates VIP indicator."""
        unlocked, msg, cache = MacLicenseManager.check_auto_unlock()
        if unlocked:
            key = cache.get("key") or cache.get("license_key") or "VIP"
            masked = key[:7] + "..." + key[-4:] if len(key) >= 11 else key
            self.lbl_vip_header_badge.configure(
                text=f"● VIP UNLOCKED ({masked})",
                text_color="#34D399"
            )
        else:
            self.lbl_vip_header_badge.configure(
                text="⚡ 1-Key macOS Registration",
                text_color=COLOR_WARNING
            )

    def on_toggle_language(self):
        new_lang = toggle_language()
        lang_text = "🌐 🇮🇩 ID" if new_lang == "id" else "🌐 🇬🇧 EN"
        self.btn_lang_toggle.configure(text=lang_text)

    def update_ui_language(self, lang: str):
        self.title(t("app_title"))
        self.lbl_brand_title.configure(text=t("header_brand_title"))
        self.lbl_brand_subtitle.configure(text=t("header_brand_subtitle"))
        self.btn_browse_folder.configure(text=t("btn_change_folder"))
        self.lbl_nav_heading.configure(text=t("nav_main_heading"))
        self.lbl_vip_badge_title.configure(text=t("vip_badge_title"))
        self.lbl_vip_badge_version.configure(text=t("vip_badge_version"))

        for tab_id, btn in self.nav_buttons.items():
            key = self.NAV_KEYS.get(tab_id)
            if key:
                btn.configure(text=t(key))

        curr_folder = self.health_suite.ts4_user_folder or t("folder_not_found")
        short_folder = curr_folder if len(curr_folder) < 42 else "..." + curr_folder[-38:]
        self.lbl_folder_path.configure(text=f"📂 {short_folder}")

    def switch_tab(self, tab_id: str):
        if tab_id not in self.tab_frames:
            return

        for tid, btn in self.nav_buttons.items():
            if tid == tab_id:
                btn.configure(
                    fg_color="#182A45",
                    text_color=NEON_CYAN_LIGHT,
                    border_width=1,
                    border_color=NEON_CYAN
                )
            else:
                btn.configure(
                    fg_color="transparent",
                    text_color=TEXT_SECONDARY,
                    border_width=0
                )

        if self.active_tab_id in self.tab_frames:
            self.tab_frames[self.active_tab_id].pack_forget()

        self.tab_frames[tab_id].pack(fill="both", expand=True)
        self.active_tab_id = tab_id

    def browse_folder(self):
        initial = self.health_suite.ts4_user_folder or os.path.expanduser("~/Documents/Electronic Arts")
        path = filedialog.askdirectory(title=t("folder_dialog_title"), initialdir=initial)
        if path and os.path.isdir(path):
            self.health_suite.ts4_user_folder = os.path.abspath(path)
            self.health_suite.mods_folder = os.path.join(self.health_suite.ts4_user_folder, "Mods")
            self.health_suite.saves_folder = os.path.join(self.health_suite.ts4_user_folder, "saves")
            self.health_suite.quarantine_folder = os.path.join(self.health_suite.ts4_user_folder, "Quarantine_WeduGames")

            # Re-initialize tab diagnostics
            self.health_suite.graphics_diag = GraphicsDiagnostic(self.health_suite.ts4_user_folder)
            self.tab_frames["graphics"].graphics_diag = self.health_suite.graphics_diag
            self.tab_frames["graphics"].refresh_all()

            short_p = path if len(path) < 42 else "..." + path[-38:]
            self.lbl_folder_path.configure(text=f"📂 {short_p}")

            messagebox.showinfo(t("folder_updated_title"), t("folder_updated_msg", path=path))
