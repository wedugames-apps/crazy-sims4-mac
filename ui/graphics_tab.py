"""
==============================================================================
Crazy Doctor for The Sims 4 (macOS Edition) - Graphics & Metal Tab
==============================================================================
Features:
- Apple Metal API pipeline inspector
- Metal Shader Cache (~/Library/Caches/com.ea.TheSims4/) & Localthumbcache Purger
- MacBook & iMac Thermal Limiter (60Hz Retina / 120Hz Liquid Retina ProMotion)
"""

import os
from tkinter import messagebox
import customtkinter as ctk

from ui.theme import (
    BG_CARD, BORDER_COLOR, NEON_CYAN, ELECTRIC_BLUE,
    COLOR_HEALTHY, COLOR_WARNING, COLOR_CRITICAL,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, get_font, neon_btn, format_bytes
)
from diagnostics.health_suite import MasterHealthSuite
from core.i18n import t


class GraphicsTab(ctk.CTkFrame):
    """Native macOS Apple Metal API and MacBook thermal limiter tab."""

    def __init__(self, master, health_suite: MasterHealthSuite):
        super().__init__(master, fg_color="transparent")
        self.health_suite = health_suite
        self.graphics_diag = health_suite.graphics_diag
        self._build_ui()
        self.refresh_all()

    def _build_ui(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=15)

        # 1. Apple Metal API Renderer Section
        sec_metal = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        sec_metal.pack(fill="x", pady=(0, 15))

        m_head = ctk.CTkFrame(sec_metal, fg_color="transparent")
        m_head.pack(fill="x", padx=20, pady=(15, 10))

        self.lbl_sec_dx = ctk.CTkLabel(
            m_head, text=t("gfx_sec_dx_title"),
            font=get_font(14, "bold"), text_color=NEON_CYAN
        )
        self.lbl_sec_dx.pack(side="left")

        self.lbl_metal_status = ctk.CTkLabel(
            m_head, text=t("gfx_dx_checking"),
            font=get_font(12, "bold"), text_color=COLOR_HEALTHY
        )
        self.lbl_metal_status.pack(side="right")

        self.lbl_metal_desc = ctk.CTkLabel(
            sec_metal,
            text=t("gfx_dx_desc"),
            font=get_font(11), text_color=TEXT_SECONDARY, wraplength=760, justify="left"
        )
        self.lbl_metal_desc.pack(anchor="w", padx=20, pady=(0, 10))

        m_btn_box = ctk.CTkFrame(sec_metal, fg_color="transparent")
        m_btn_box.pack(anchor="w", padx=20, pady=(0, 15))

        self.btn_metal_opt = neon_btn(
            m_btn_box, text="⚡ Optimize Apple Metal Pipeline",
            command=self.optimize_metal,
            style="cyan", width=250, height=32
        )
        self.btn_metal_opt.pack(side="left", padx=(0, 10))

        # 2. Metal Shader & Thumbnail Cache Purger
        sec_cache = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        sec_cache.pack(fill="x", pady=(0, 15))

        c_head = ctk.CTkFrame(sec_cache, fg_color="transparent")
        c_head.pack(fill="x", padx=20, pady=(15, 10))

        self.lbl_sec_cache = ctk.CTkLabel(
            c_head, text=t("gfx_sec_cache_title"),
            font=get_font(14, "bold"), text_color=COLOR_HEALTHY
        )
        self.lbl_sec_cache.pack(side="left")

        self.btn_purge = neon_btn(
            c_head, text=t("gfx_btn_purge"),
            command=self.run_cache_purge,
            style="green", width=210, height=32
        )
        self.btn_purge.pack(side="right")

        self.lbl_cache_summary = ctk.CTkLabel(
            sec_cache, text=t("gfx_cache_inspecting"),
            font=get_font(12, "bold"), text_color=TEXT_PRIMARY
        )
        self.lbl_cache_summary.pack(anchor="w", padx=20, pady=(0, 4))

        self.lbl_cache_desc = ctk.CTkLabel(
            sec_cache,
            text=t("gfx_cache_desc"),
            font=get_font(11), text_color=TEXT_SECONDARY, wraplength=760, justify="left"
        )
        self.lbl_cache_desc.pack(anchor="w", padx=20, pady=(0, 15))

        # 3. MacBook & iMac Thermal Limiter Section
        sec_fps = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        sec_fps.pack(fill="x", pady=(0, 15))

        f_head = ctk.CTkFrame(sec_fps, fg_color="transparent")
        f_head.pack(fill="x", padx=20, pady=(15, 10))

        self.lbl_sec_fps = ctk.CTkLabel(
            f_head, text=t("gfx_sec_fps_title"),
            font=get_font(14, "bold"), text_color=COLOR_WARNING
        )
        self.lbl_sec_fps.pack(side="left")

        self.lbl_fps_status = ctk.CTkLabel(
            f_head, text="",
            font=get_font(12, "bold"), text_color=COLOR_HEALTHY
        )
        self.lbl_fps_status.pack(side="right")

        self.lbl_fps_desc = ctk.CTkLabel(
            sec_fps,
            text=t("gfx_fps_desc"),
            font=get_font(11), text_color=TEXT_SECONDARY, wraplength=760, justify="left"
        )
        self.lbl_fps_desc.pack(anchor="w", padx=20, pady=(0, 12))

        # MacBook Presets Box
        preset_box = ctk.CTkFrame(sec_fps, fg_color="transparent")
        preset_box.pack(anchor="w", padx=20, pady=(0, 15))

        self.btn_fps_60 = neon_btn(
            preset_box, text="⚡ 60 FPS (Retina Standard)",
            command=lambda: self.set_fps_limit(60),
            style="amber", width=200, height=32
        )
        self.btn_fps_60.pack(side="left", padx=(0, 10))

        self.btn_fps_120 = neon_btn(
            preset_box, text="⚡ 120 FPS (Liquid Retina ProMotion)",
            command=lambda: self.set_fps_limit(120),
            style="purple", width=250, height=32
        )
        self.btn_fps_120.pack(side="left", padx=(0, 10))

        self.btn_fps_30 = neon_btn(
            preset_box, text="🔋 30 FPS (Battery Saver)",
            command=lambda: self.set_fps_limit(30),
            style="secondary", width=180, height=32
        )
        self.btn_fps_30.pack(side="left")

    def refresh_all(self):
        if not self.graphics_diag:
            return

        # 1. Metal Status
        mode_info = self.graphics_diag.get_graphics_mode()
        self.lbl_metal_status.configure(text=mode_info.get("mode", "Apple Metal API"))

        # 2. Cache Inspection
        cache_items = self.graphics_diag.inspect_cache_items()
        total_b = sum(c["size"] for c in cache_items)
        self.lbl_cache_summary.configure(
            text=t("gfx_cache_summary", size=format_bytes(total_b), count=len(cache_items))
        )

        # 3. FPS Limiter Status
        fps_info = self.graphics_diag.inspect_fps_limit()
        if fps_info.get("is_fps_limited"):
            disp = fps_info.get("display_profile") or "Limited"
            self.lbl_fps_status.configure(
                text=t("gfx_fps_status_active", limit=disp),
                text_color=COLOR_HEALTHY
            )
        else:
            self.lbl_fps_status.configure(
                text=t("gfx_fps_status_uncapped"),
                text_color=COLOR_CRITICAL
            )

    def optimize_metal(self):
        if not self.graphics_diag:
            return
        ok, msg = self.graphics_diag.set_metal_mode(enable_metal=True)
        self.refresh_all()
        if ok:
            messagebox.showinfo(t("gfx_dialog_dx_title"), msg)
        else:
            messagebox.showerror(t("gfx_dialog_dx_title"), msg)

    def run_cache_purge(self):
        if not self.graphics_diag:
            return
        c, b = self.graphics_diag.purge_cache()
        self.refresh_all()
        messagebox.showinfo(
            t("gfx_cache_purged_title"),
            t("gfx_cache_purged_msg", count=c, size=format_bytes(b))
        )

    def set_fps_limit(self, target_fps: int):
        if not self.graphics_diag:
            return
        ok, msg = self.graphics_diag.apply_fps_limiter(target_fps=target_fps, force_vsync=True)
        self.refresh_all()
        if ok:
            messagebox.showinfo(t("gfx_dialog_fps_title"), t("gfx_dialog_fps_success", fps=target_fps))
        else:
            messagebox.showerror(t("gfx_dialog_fps_title"), t("gfx_dialog_fps_error", error=msg))
