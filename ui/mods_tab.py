"""
==============================================================================
Crazy The Sims 4 Project - Mods & CC Tab
==============================================================================
Deep CC inspection & optimization tools:
- High-Poly CC Lag Bomb Profiler (> 30k polygons)
- Missing Parent Mesh Hunter (Orphan recolors)
- Townie CC Sanitizer (AllowForRandom = 0)
- Texture Downsampler (4K/8K -> 2K Lanczos)
- 50/50 Binary Search Automator
"""

import os
import threading
from tkinter import messagebox
import customtkinter as ctk

from ui.theme import (
    BG_CARD, BORDER_COLOR, NEON_CYAN, ELECTRIC_BLUE,
    COLOR_HEALTHY, COLOR_WARNING, COLOR_CRITICAL,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, get_font, format_bytes, neon_btn
)
from diagnostics.health_suite import MasterHealthSuite
from diagnostics.search_5050 import Method5050Automator
from core.dbpf import DBPFPackage
from core.texture import TextureProcessor
from core.i18n import t


class ModsTab(ctk.CTkFrame):
    """3D mesh profiling, parent mesh hunting, townie sanitizing, and 50/50 search."""

    def __init__(self, master, health_suite: MasterHealthSuite):
        super().__init__(master, fg_color="transparent")
        self.health_suite = health_suite
        self.automator_5050 = Method5050Automator(health_suite.mods_folder) if health_suite.mods_folder else None
        self._last_mesh_res = None
        self._last_townie_stats = None
        self._last_tex_stats = None

        self._build_ui()

    def _build_ui(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=15)

        # 1. High-Poly CC Lag Bomb Profiler & Missing Mesh Section
        sec_mesh = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        sec_mesh.pack(fill="x", pady=(0, 15))

        m_head = ctk.CTkFrame(sec_mesh, fg_color="transparent")
        m_head.pack(fill="x", padx=20, pady=(15, 10))

        self.lbl_mesh_title = ctk.CTkLabel(
            m_head, text=t("mods_sec_mesh_title"),
            font=get_font(14, "bold"), text_color=NEON_CYAN
        )
        self.lbl_mesh_title.pack(side="left")

        self.btn_mesh_scan = neon_btn(
            m_head, text=t("mods_btn_mesh_scan"),
            command=self.run_mesh_profile,
            style="cyan",
            width=170, height=32
        )
        self.btn_mesh_scan.pack(side="right")

        self.lbl_mesh_status = ctk.CTkLabel(
            sec_mesh,
            text=t("mods_mesh_desc"),
            font=get_font(11), text_color=TEXT_SECONDARY
        )
        self.lbl_mesh_status.pack(anchor="w", padx=20, pady=(0, 10))

        self.txt_mesh_results = ctk.CTkTextbox(
            sec_mesh, height=100, fg_color="#0A111E",
            font=get_font(11, family="Consolas"), text_color="#E2E8F0"
        )
        self.txt_mesh_results.pack(fill="x", padx=20, pady=(0, 15))
        self.txt_mesh_results.insert("1.0", t("mods_mesh_placeholder"))
        self.txt_mesh_results.configure(state="disabled")

        # 2. Townie CC Sanitizer (AllowForRandom = 0)
        sec_townie = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        sec_townie.pack(fill="x", pady=(0, 15))

        t_head = ctk.CTkFrame(sec_townie, fg_color="transparent")
        t_head.pack(fill="x", padx=20, pady=(15, 10))

        self.lbl_townie_title = ctk.CTkLabel(
            t_head, text=t("mods_sec_townie_title"),
            font=get_font(14, "bold"), text_color=COLOR_HEALTHY
        )
        self.lbl_townie_title.pack(side="left")

        self.btn_townie = neon_btn(
            t_head, text=t("mods_btn_townie"),
            command=self.run_townie_sanitizer,
            style="green",
            width=190, height=32
        )
        self.btn_townie.pack(side="right")

        self.lbl_townie_status = ctk.CTkLabel(
            sec_townie,
            text=t("mods_townie_desc"),
            font=get_font(11), text_color=TEXT_SECONDARY
        )
        self.lbl_townie_status.pack(anchor="w", padx=20, pady=(0, 15))

        # 3. Texture Downsampler (4K/8K to 2K Lanczos)
        sec_tex = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        sec_tex.pack(fill="x", pady=(0, 15))

        tex_head = ctk.CTkFrame(sec_tex, fg_color="transparent")
        tex_head.pack(fill="x", padx=20, pady=(15, 10))

        self.lbl_tex_title = ctk.CTkLabel(
            tex_head, text=t("mods_sec_tex_title"),
            font=get_font(14, "bold"), text_color="#A855F7"
        )
        self.lbl_tex_title.pack(side="left")

        self.btn_opt_tex = neon_btn(
            tex_head, text=t("mods_btn_opt_tex"),
            command=self.run_texture_optimization,
            style="purple",
            width=220, height=32
        )
        self.btn_opt_tex.pack(side="right")

        self.lbl_tex_status = ctk.CTkLabel(
            sec_tex,
            text=t("mods_tex_desc"),
            font=get_font(11), text_color=TEXT_SECONDARY
        )
        self.lbl_tex_status.pack(anchor="w", padx=20, pady=(0, 15))

        # 4. 50/50 Binary Search Wizard
        sec_5050 = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        sec_5050.pack(fill="x")

        f_head = ctk.CTkFrame(sec_5050, fg_color="transparent")
        f_head.pack(fill="x", padx=20, pady=(15, 10))

        self.lbl_5050_title = ctk.CTkLabel(
            f_head, text=t("mods_sec_5050_title"),
            font=get_font(14, "bold"), text_color=COLOR_WARNING
        )
        self.lbl_5050_title.pack(side="left")

        self.lbl_5050_step = ctk.CTkLabel(
            f_head, text=t("mods_5050_step_inactive"),
            font=get_font(12, "bold"), text_color=TEXT_PRIMARY
        )
        self.lbl_5050_step.pack(side="right")

        f_body = ctk.CTkFrame(sec_5050, fg_color="transparent")
        f_body.pack(fill="x", padx=20, pady=(0, 15))

        self.lbl_5050_desc = ctk.CTkLabel(
            f_body,
            text=t("mods_5050_desc_default"),
            font=get_font(11), text_color=TEXT_SECONDARY, justify="left"
        )
        self.lbl_5050_desc.pack(anchor="w", pady=(0, 10))

        f_actions = ctk.CTkFrame(f_body, fg_color="transparent")
        f_actions.pack(anchor="w")

        self.btn_5050_start = neon_btn(
            f_actions, text=t("mods_btn_5050_start"),
            command=self.start_5050,
            style="blue",
            width=180, height=32
        )
        self.btn_5050_start.pack(side="left", padx=(0, 10))

        self.btn_5050_broken = neon_btn(
            f_actions, text=t("mods_btn_5050_broken"),
            command=lambda: self.record_5050(True),
            style="red",
            width=160, height=32
        )
        self.btn_5050_broken.pack(side="left", padx=(0, 10))

        self.btn_5050_clean = neon_btn(
            f_actions, text=t("mods_btn_5050_clean"),
            command=lambda: self.record_5050(False),
            style="green",
            width=160, height=32
        )
        self.btn_5050_clean.pack(side="left", padx=(0, 10))

        self.btn_5050_cancel = neon_btn(
            f_actions, text=t("mods_btn_5050_cancel"),
            command=self.cancel_5050,
            style="secondary",
            width=150, height=32
        )
        self.btn_5050_cancel.pack(side="left")

        self._refresh_5050_ui()

    def run_mesh_profile(self):
        hunter = self.health_suite.mesh_hunter
        if not hunter:
            messagebox.showwarning(t("common_notice"), t("doc_notice_mods_missing"))
            return

        self.lbl_mesh_status.configure(text=t("mods_mesh_scanning_bg"))
        self.txt_mesh_results.configure(state="normal")
        self.txt_mesh_results.delete("1.0", "end")
        self.txt_mesh_results.insert("1.0", t("mods_mesh_scanning"))
        self.txt_mesh_results.configure(state="disabled")

        def _worker():
            res = hunter.scan_mods(max_packages=300)
            self.after(0, lambda: self._on_mesh_profile_done(res))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_mesh_profile_done(self, res):
        self._last_mesh_res = res
        self.txt_mesh_results.configure(state="normal")
        self.txt_mesh_results.delete("1.0", "end")

        out = []
        out.append(t("mods_mesh_res_header"))
        out.append(t("mods_mesh_res_summary", pkg_count=res['scanned_count'], mesh_count=res['scanned_count']))
        out.append(f"• Lag Bombs: {res['lag_bomb_count']}")
        out.append(f"• Orphan Recolors: {res['orphan_recolor_count']}\n")

        if res["lag_bombs"]:
            out.append(t("mods_mesh_res_lag_bombs"))
            for b in res["lag_bombs"][:10]:
                out.append(f" • {b.filename}: {b.max_polygons:,} polygons")

        if res["orphan_recolors"]:
            out.append("\n" + t("mods_mesh_res_orphans"))
            for o in res["orphan_recolors"][:10]:
                out.append(f" • {o.filename} (References missing mesh ID 0x{o.missing_mesh_instances[0]:X})")

        if not res["lag_bombs"] and not res["orphan_recolors"]:
            out.append(t("mods_mesh_res_clean"))

        self.txt_mesh_results.insert("1.0", "\n".join(out))
        self.txt_mesh_results.configure(state="disabled")
        self.lbl_mesh_status.configure(
            text=t("mods_mesh_complete", lag_bombs=res['lag_bomb_count'], orphans=res['orphan_recolor_count'])
        )

    def run_townie_sanitizer(self):
        sanitizer = self.health_suite.townie_sanitizer
        if not sanitizer:
            messagebox.showwarning(t("common_notice"), t("doc_notice_mods_missing"))
            return

        confirm = messagebox.askyesno(
            t("mods_townie_confirm_title"),
            t("mods_townie_confirm_msg")
        )
        if not confirm:
            return

        self.btn_townie.configure(state="disabled", text=t("mods_btn_townie_running"))

        def _worker():
            pkg_c, casp_c = sanitizer.sanitize_all_townie_cc(max_packages=500)
            self.after(0, lambda: self._on_townie_done(pkg_c, casp_c))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_townie_done(self, pkg_c, casp_c):
        self._last_townie_stats = (pkg_c, casp_c)
        self.btn_townie.configure(state="normal", text=t("mods_btn_townie"))
        messagebox.showinfo(
            t("mods_townie_done_title"),
            t("mods_townie_done_msg", pkgs=pkg_c, casps=casp_c)
        )
        self.lbl_townie_status.configure(text=t("mods_townie_status_done", pkgs=pkg_c, casps=casp_c))

    def run_texture_optimization(self):
        mods_dir = self.health_suite.mods_folder
        if not mods_dir or not os.path.isdir(mods_dir):
            messagebox.showwarning(t("common_notice"), t("doc_notice_mods_missing"))
            return

        confirm = messagebox.askyesno(
            t("mods_tex_confirm_title"),
            t("mods_tex_confirm_msg")
        )
        if not confirm:
            return

        def _worker():
            optimized = 0
            freed = 0
            for root, _, files in os.walk(mods_dir):
                for f in files:
                    if f.lower().endswith(".package"):
                        p = os.path.join(root, f)
                        try:
                            pkg = DBPFPackage(p)
                            down_c, b_saved = TextureProcessor.optimize_package_textures(pkg, max_dim=2048)
                            if down_c > 0:
                                pkg.save_atomic(p)
                                optimized += down_c
                                freed += b_saved
                        except Exception:
                            pass
            self.after(0, lambda: self._on_texture_done(optimized, freed))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_texture_done(self, count, freed):
        self._last_tex_stats = (count, freed)
        messagebox.showinfo(
            t("mods_tex_done_title"),
            t("mods_tex_done_msg", count=count, freed=format_bytes(freed))
        )
        self.lbl_tex_status.configure(text=t("mods_tex_status_done", count=count, freed=format_bytes(freed)))

    def _refresh_5050_ui(self):
        if not self.automator_5050:
            return

        if self.automator_5050.is_active:
            step = self.automator_5050.current_step
            suspects = len(self.automator_5050.suspect_pool)
            self.lbl_5050_step.configure(
                text=t("mods_5050_step_progress", step=step, active=len(self.automator_5050.active_batch), suspects=suspects),
                text_color=TEXT_PRIMARY
            )
            self.lbl_5050_desc.configure(text=t("mods_5050_desc_progress"))
            self.btn_5050_broken.configure(state="normal", text=t("mods_btn_5050_broken"))
            self.btn_5050_clean.configure(state="normal", text=t("mods_btn_5050_clean"))
            self.btn_5050_start.configure(state="disabled", text=t("mods_btn_5050_start"))
            self.btn_5050_cancel.configure(text=t("mods_btn_5050_cancel"))
        elif self.automator_5050.identified_culprit:
            self.lbl_5050_step.configure(text=t("mods_5050_step_isolated"), text_color=COLOR_CRITICAL)
            self.lbl_5050_desc.configure(text=t("mods_5050_desc_isolated", mod=self.automator_5050.identified_culprit))
            self.btn_5050_broken.configure(state="disabled", text=t("mods_btn_5050_broken"))
            self.btn_5050_clean.configure(state="disabled", text=t("mods_btn_5050_clean"))
            self.btn_5050_start.configure(state="normal", text=t("mods_btn_5050_start"))
            self.btn_5050_cancel.configure(text=t("mods_btn_5050_cancel"))
        else:
            self.lbl_5050_step.configure(text=t("mods_5050_step_inactive"), text_color=TEXT_PRIMARY)
            self.lbl_5050_desc.configure(text=t("mods_5050_desc_default"))
            self.btn_5050_broken.configure(state="disabled", text=t("mods_btn_5050_broken"))
            self.btn_5050_clean.configure(state="disabled", text=t("mods_btn_5050_clean"))
            self.btn_5050_start.configure(state="normal", text=t("mods_btn_5050_start"))
            self.btn_5050_cancel.configure(text=t("mods_btn_5050_cancel"))

    def start_5050(self):
        if not self.automator_5050:
            return
        ok, msg = self.automator_5050.start_session()
        messagebox.showinfo(t("mods_5050_dialog_title"), msg)
        self._refresh_5050_ui()

    def record_5050(self, glitch_present: bool):
        if not self.automator_5050:
            return
        ok, msg = self.automator_5050.record_test_result(glitch_present)
        messagebox.showinfo(t("mods_5050_dialog_title"), msg)
        self._refresh_5050_ui()

    def cancel_5050(self):
        if not self.automator_5050:
            return
        ok, msg = self.automator_5050.cancel_and_restore()
        messagebox.showinfo(t("mods_5050_dialog_title"), msg)
        self._refresh_5050_ui()

    def update_ui_language(self):
        """Dynamically re-applies translations to all labels and buttons."""
        self.lbl_mesh_title.configure(text=t("mods_sec_mesh_title"))
        self.btn_mesh_scan.configure(text=t("mods_btn_mesh_scan"))
        if self._last_mesh_res:
            self.lbl_mesh_status.configure(
                text=t("mods_mesh_complete", lag_bombs=self._last_mesh_res['lag_bomb_count'], orphans=self._last_mesh_res['orphan_recolor_count'])
            )
        else:
            self.lbl_mesh_status.configure(text=t("mods_mesh_desc"))

        self.lbl_townie_title.configure(text=t("mods_sec_townie_title"))
        self.btn_townie.configure(text=t("mods_btn_townie"))
        if self._last_townie_stats:
            self.lbl_townie_status.configure(text=t("mods_townie_status_done", pkgs=self._last_townie_stats[0], casps=self._last_townie_stats[1]))
        else:
            self.lbl_townie_status.configure(text=t("mods_townie_desc"))

        self.lbl_tex_title.configure(text=t("mods_sec_tex_title"))
        self.btn_opt_tex.configure(text=t("mods_btn_opt_tex"))
        if self._last_tex_stats:
            self.lbl_tex_status.configure(text=t("mods_tex_status_done", count=self._last_tex_stats[0], freed=format_bytes(self._last_tex_stats[1])))
        else:
            self.lbl_tex_status.configure(text=t("mods_tex_desc"))

        self.lbl_5050_title.configure(text=t("mods_sec_5050_title"))
        self._refresh_5050_ui()
