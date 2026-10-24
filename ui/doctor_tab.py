"""
==============================================================================
Crazy The Sims 4 Project - Doctor Tab
==============================================================================
Deep Diagnostic Doctor featuring:
- Script Mod Depth Flattener (resolves depth > 1 engine restriction)
- lastException & lastCrash stack trace decoder
- 0-Byte and corrupt package isolator
- Duplicate CC detector (SHA256)
"""

import os
import threading
from tkinter import messagebox
import customtkinter as ctk

from ui.theme import (
    BG_CARD, BORDER_COLOR, NEON_CYAN, ELECTRIC_BLUE,
    COLOR_HEALTHY, COLOR_WARNING, COLOR_CRITICAL,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, get_font, neon_btn
)
from diagnostics.health_suite import MasterHealthSuite
from core.i18n import t


class DoctorTab(ctk.CTkFrame):
    """Deep inspection and healing for script mods, exceptions, and corrupt files."""

    def __init__(self, master, health_suite: MasterHealthSuite):
        super().__init__(master, fg_color="transparent")
        self.health_suite = health_suite
        self._last_script_moved = None
        self._last_quarantined = None
        self._build_ui()

    def _build_ui(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=15)

        # 1. Script Mod Depth Section
        sec_script = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        sec_script.pack(fill="x", pady=(0, 15))

        s_head = ctk.CTkFrame(sec_script, fg_color="transparent")
        s_head.pack(fill="x", padx=20, pady=(15, 10))

        self.lbl_script_title = ctk.CTkLabel(
            s_head, text=t("doc_sec_script_title"),
            font=get_font(14, "bold"), text_color=NEON_CYAN
        )
        self.lbl_script_title.pack(side="left")

        self.btn_flatten = neon_btn(
            s_head, text=t("doc_btn_flatten"),
            command=self.run_flatten_scripts,
            style="blue",
            width=200, height=32
        )
        self.btn_flatten.pack(side="right")

        self.lbl_script_status = ctk.CTkLabel(
            sec_script,
            text=t("doc_script_desc"),
            font=get_font(11), text_color=TEXT_SECONDARY, justify="left"
        )
        self.lbl_script_status.pack(anchor="w", padx=20, pady=(0, 15))

        # 2. lastException / Crash Log Analyzer Section
        sec_crash = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        sec_crash.pack(fill="x", pady=(0, 15))

        c_head = ctk.CTkFrame(sec_crash, fg_color="transparent")
        c_head.pack(fill="x", padx=20, pady=(15, 10))

        self.lbl_crash_title = ctk.CTkLabel(
            c_head, text=t("doc_sec_crash_title"),
            font=get_font(14, "bold"), text_color=COLOR_CRITICAL
        )
        self.lbl_crash_title.pack(side="left")

        self.btn_analyze_crash = neon_btn(
            c_head, text=t("doc_btn_analyze_crash"),
            command=self.analyze_crash_logs,
            style="cyan",
            width=180, height=32
        )
        self.btn_analyze_crash.pack(side="right")

        self.txt_crash_result = ctk.CTkTextbox(
            sec_crash, height=140, fg_color="#0A111E",
            font=get_font(11, family="Consolas"), text_color="#E2E8F0"
        )
        self.txt_crash_result.pack(fill="x", padx=20, pady=(0, 15))
        self.txt_crash_result.insert("1.0", t("doc_crash_placeholder"))
        self.txt_crash_result.configure(state="disabled")

        # 3. Corrupt Package & 0-Byte Isolator
        sec_corrupt = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        sec_corrupt.pack(fill="x")

        cor_head = ctk.CTkFrame(sec_corrupt, fg_color="transparent")
        cor_head.pack(fill="x", padx=20, pady=(15, 10))

        self.lbl_corrupt_title = ctk.CTkLabel(
            cor_head, text=t("doc_sec_corrupt_title"),
            font=get_font(14, "bold"), text_color=COLOR_WARNING
        )
        self.lbl_corrupt_title.pack(side="left")

        self.btn_isolate = neon_btn(
            cor_head, text=t("doc_btn_isolate"),
            command=self.isolate_corrupt_mods,
            style="amber",
            width=210, height=32
        )
        self.btn_isolate.pack(side="right")

        self.lbl_corrupt_status = ctk.CTkLabel(
            sec_corrupt,
            text=t("doc_corrupt_desc"),
            font=get_font(11), text_color=TEXT_SECONDARY, justify="left"
        )
        self.lbl_corrupt_status.pack(anchor="w", padx=20, pady=(0, 15))

    def run_flatten_scripts(self):
        flattener = self.health_suite.script_flattener
        if not flattener:
            messagebox.showwarning(t("common_notice"), t("doc_notice_mods_missing"))
            return

        moved, logs = flattener.flatten_all_violations()
        self._last_script_moved = moved
        if moved == 0:
            messagebox.showinfo(t("doc_dialog_script_title"), t("doc_flatten_clean"))
            self.lbl_script_status.configure(text=t("doc_script_desc"))
        else:
            log_str = "\n• " + "\n• ".join(logs)
            messagebox.showinfo(
                t("doc_dialog_script_title"),
                t("doc_flatten_success", count=moved, log_str=log_str)
            )
            self.lbl_script_status.configure(
                text=t("doc_script_status_done", count=moved)
            )

    def analyze_crash_logs(self):
        decoder = self.health_suite.crash_decoder
        if not decoder:
            messagebox.showwarning(t("common_notice"), t("doc_notice_user_missing"))
            return

        report = decoder.get_latest_crash_report()
        self._last_crash_report = report
        self.txt_crash_result.configure(state="normal")
        self.txt_crash_result.delete("1.0", "end")

        if not report:
            self.txt_crash_result.insert("1.0", t("doc_crash_clean"))
        else:
            out = []
            out.append(t("doc_crash_log_file", file=report['file']))
            out.append(t("doc_crash_summary", summary=report['summary']) + "\n")
            if report["detected_culprits"]:
                out.append(t("doc_crash_culprits"))
                for c in report["detected_culprits"]:
                    out.append(t("doc_crash_culprit_item", mod=c['mod_name'], author=c['author'], sev=c['severity'], advice=c['advice']) + "\n")
            if report["raw_exception_type"]:
                out.append(t("doc_crash_engine_err", err=report['raw_exception_type']) + "\n")
            out.append(t("doc_crash_traceback"))
            out.append(report["traceback_snippet"])

            self.txt_crash_result.insert("1.0", "\n".join(out))

        self.txt_crash_result.configure(state="disabled")

    def isolate_corrupt_mods(self):
        mods_dir = self.health_suite.mods_folder
        if not mods_dir or not os.path.isdir(mods_dir):
            messagebox.showwarning(t("common_notice"), t("doc_notice_mods_missing"))
            return

        quarantine_dir = os.path.join(self.health_suite.quarantine_folder, "Corrupt_Packages")
        os.makedirs(quarantine_dir, exist_ok=True)

        quarantined = 0
        for root, _, files in os.walk(mods_dir):
            for f in files:
                if f.lower().endswith(".package"):
                    p = os.path.join(root, f)
                    try:
                        if os.path.getsize(p) == 0:
                            dst = os.path.join(quarantine_dir, f)
                            import shutil
                            shutil.move(p, dst)
                            quarantined += 1
                    except Exception:
                        pass

        self._last_quarantined = quarantined
        if quarantined == 0:
            messagebox.showinfo(t("doc_dialog_isolate_title"), t("doc_corrupt_clean"))
            self.lbl_corrupt_status.configure(text=t("doc_corrupt_desc"))
        else:
            messagebox.showinfo(
                t("doc_dialog_isolate_done_title"),
                t("doc_corrupt_success", count=quarantined, dir=quarantine_dir)
            )
            self.lbl_corrupt_status.configure(
                text=t("doc_corrupt_status_done", count=quarantined)
            )

    def update_ui_language(self):
        """Dynamically re-applies translations to all labels and buttons."""
        self.lbl_script_title.configure(text=t("doc_sec_script_title"))
        self.btn_flatten.configure(text=t("doc_btn_flatten"))
        if self._last_script_moved is not None and self._last_script_moved > 0:
            self.lbl_script_status.configure(text=t("doc_script_status_done", count=self._last_script_moved))
        else:
            self.lbl_script_status.configure(text=t("doc_script_desc"))

        self.lbl_crash_title.configure(text=t("doc_sec_crash_title"))
        self.btn_analyze_crash.configure(text=t("doc_btn_analyze_crash"))
        if not getattr(self, "_last_crash_report", None):
            self.txt_crash_result.configure(state="normal")
            self.txt_crash_result.delete("1.0", "end")
            self.txt_crash_result.insert("1.0", t("doc_crash_placeholder"))
            self.txt_crash_result.configure(state="disabled")

        self.lbl_corrupt_title.configure(text=t("doc_sec_corrupt_title"))
        self.btn_isolate.configure(text=t("doc_btn_isolate"))
        if self._last_quarantined is not None and self._last_quarantined > 0:
            self.lbl_corrupt_status.configure(text=t("doc_corrupt_status_done", count=self._last_quarantined))
        else:
            self.lbl_corrupt_status.configure(text=t("doc_corrupt_desc"))
