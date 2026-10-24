"""
==============================================================================
Crazy The Sims 4 Project - Dashboard Tab
==============================================================================
Modern Neon Dashboard featuring:
- 1-Click Full System Scan
- Aggregate Health Score (0-100)
- Health Status Cards (Critical Red, Warning Yellow, Healthy Green)
- 1-Click Auto-Fix All with safe quarantine backup
"""

import os
import threading
import tkinter as tk
from tkinter import messagebox
import customtkinter as ctk

from ui.theme import (
    BG_DARK, BG_CARD, BG_CARD_HOVER, BORDER_COLOR,
    NEON_CYAN, NEON_CYAN_LIGHT, ELECTRIC_BLUE,
    COLOR_HEALTHY, COLOR_WARNING, COLOR_CRITICAL,
    COLOR_HEALTHY_BG, COLOR_WARNING_BG, COLOR_CRITICAL_BG,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, get_font,
    neon_btn, NEON_BTN_CYAN, NEON_BTN_GREEN
)
from diagnostics.health_suite import MasterHealthSuite, HealthIssue
from core.i18n import t


class DashboardTab(ctk.CTkFrame):
    """Main Dashboard view displaying real-time system health and 1-Click actions."""

    def __init__(self, master, health_suite: MasterHealthSuite, on_navigate_tab=None):
        super().__init__(master, fg_color="transparent")
        self.health_suite = health_suite
        self.on_navigate_tab = on_navigate_tab
        self.is_scanning = False

        self._build_ui()

    def _build_ui(self):
        # Scrollable container for fluid layout
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=15)

        # Top Action & Score Banner
        banner = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        banner.pack(fill="x", pady=(0, 15))

        banner_content = ctk.CTkFrame(banner, fg_color="transparent")
        banner_content.pack(fill="x", padx=25, pady=20)

        # Left: Score Gauge
        score_box = ctk.CTkFrame(banner_content, fg_color="#0A111E", corner_radius=10, width=150, height=130)
        score_box.pack(side="left", padx=(0, 25))
        score_box.pack_propagate(False)

        self.lbl_score_header = ctk.CTkLabel(
            score_box, text=t("dash_score_title"),
            font=get_font(11, "bold"), text_color=TEXT_MUTED
        )
        self.lbl_score_header.pack(pady=(15, 2))

        self.lbl_score = ctk.CTkLabel(
            score_box, text="100",
            font=get_font(38, "bold"), text_color=COLOR_HEALTHY
        )
        self.lbl_score.pack()

        self.lbl_status_badge = ctk.CTkLabel(
            score_box, text=t("dash_status_healthy"),
            font=get_font(10, "bold"), text_color=COLOR_HEALTHY
        )
        self.lbl_status_badge.pack(pady=(0, 10))

        # Center: System Info & Description
        info_box = ctk.CTkFrame(banner_content, fg_color="transparent")
        info_box.pack(side="left", fill="both", expand=True)

        self.lbl_main_title = ctk.CTkLabel(
            info_box, text=t("dash_title"),
            font=get_font(18, "bold"), text_color=NEON_CYAN
        )
        self.lbl_main_title.pack(anchor="w")

        self.lbl_main_desc = ctk.CTkLabel(
            info_box,
            text=t("dash_desc"),
            font=get_font(12), text_color=TEXT_SECONDARY
        )
        self.lbl_main_desc.pack(anchor="w", pady=(2, 10))

        self.lbl_last_scan = ctk.CTkLabel(
            info_box, text=t("dash_last_scan_never"),
            font=get_font(11), text_color=TEXT_MUTED
        )
        self.lbl_last_scan.pack(anchor="w")

        # Right: Quick Action Buttons
        btn_box = ctk.CTkFrame(banner_content, fg_color="transparent")
        btn_box.pack(side="right", padx=(20, 0))

        self.btn_scan = neon_btn(
            btn_box, text=t("dash_btn_scan"),
            command=self.start_full_scan,
            style="cyan",
            font=get_font(13, "bold"),
            height=42, width=190, corner_radius=8
        )
        self.btn_scan.pack(pady=(0, 10))

        self.btn_autofix = neon_btn(
            btn_box, text=t("dash_btn_autofix"),
            command=self.start_auto_fix,
            style="green",
            font=get_font(13, "bold"),
            height=42, width=190, corner_radius=8
        )
        self.btn_autofix.pack()

        # Progress bar (hidden by default)
        self.prog_bar = ctk.CTkProgressBar(self.scroll, mode="indeterminate", progress_color=NEON_CYAN)

        # 3 Status Summary Cards (Critical Red, Warning Yellow, Healthy Green)
        cards_frame = ctk.CTkFrame(self.scroll, fg_color="transparent")
        cards_frame.pack(fill="x", pady=(0, 15))
        cards_frame.columnconfigure(0, weight=1)
        cards_frame.columnconfigure(1, weight=1)
        cards_frame.columnconfigure(2, weight=1)

        # Critical Card
        self.card_crit = self._create_card(
            cards_frame, col=0, card_type="crit",
            title=t("dash_card_crit_title"),
            count_text="0", count_color=COLOR_CRITICAL,
            desc=t("dash_card_crit_desc")
        )

        # Warning Card
        self.card_warn = self._create_card(
            cards_frame, col=1, card_type="warn",
            title=t("dash_card_warn_title"),
            count_text="0", count_color=COLOR_WARNING,
            desc=t("dash_card_warn_desc")
        )

        # Healthy Card
        self.card_healthy = self._create_card(
            cards_frame, col=2, card_type="healthy",
            title=t("dash_card_healthy_title"),
            count_text=t("dash_card_healthy_optimal"), count_color=COLOR_HEALTHY,
            desc=t("dash_card_healthy_desc")
        )

        # Detailed Issues List Container
        issues_box = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        issues_box.pack(fill="both", expand=True)

        i_header = ctk.CTkFrame(issues_box, fg_color="transparent")
        i_header.pack(fill="x", padx=20, pady=(15, 10))

        self.lbl_findings_header = ctk.CTkLabel(
            i_header, text=t("dash_log_title"),
            font=get_font(14, "bold"), text_color=TEXT_PRIMARY
        )
        self.lbl_findings_header.pack(side="left")

        self.lbl_issue_count = ctk.CTkLabel(
            i_header, text=t("dash_issues_count", count=0),
            font=get_font(12, "bold"), text_color=TEXT_MUTED
        )
        self.lbl_issue_count.pack(side="right")

        # Scrollable list of findings
        self.issues_list_frame = ctk.CTkFrame(issues_box, fg_color="transparent")
        self.issues_list_frame.pack(fill="both", expand=True, padx=20, pady=(0, 20))

        self._render_empty_state()

    def _create_card(self, parent, col, card_type, title, count_text, count_color, desc):
        card = ctk.CTkFrame(parent, fg_color=BG_CARD, corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        card.grid(row=0, column=col, padx=6, sticky="nsew")

        content = ctk.CTkFrame(card, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=16, pady=16)

        lbl_title = ctk.CTkLabel(content, text=title, font=get_font(11, "bold"), text_color=TEXT_MUTED)
        lbl_title.pack(anchor="w")
        lbl_count = ctk.CTkLabel(content, text=count_text, font=get_font(26, "bold"), text_color=count_color)
        lbl_count.pack(anchor="w", pady=(4, 2))
        lbl_desc = ctk.CTkLabel(content, text=desc, font=get_font(11), text_color=TEXT_SECONDARY, wraplength=220, justify="left")
        lbl_desc.pack(anchor="w")

        card.card_type = card_type
        card.lbl_title = lbl_title
        card.lbl_count = lbl_count
        card.lbl_desc = lbl_desc
        return card

    def _render_empty_state(self):
        for w in self.issues_list_frame.winfo_children():
            w.destroy()

        empty_box = ctk.CTkFrame(self.issues_list_frame, fg_color="#0A111E", corner_radius=8)
        empty_box.pack(fill="x", pady=10)

        ctk.CTkLabel(
            empty_box,
            text=t("dash_empty_state"),
            font=get_font(12), text_color=TEXT_SECONDARY
        ).pack(pady=20)

    def start_full_scan(self):
        if self.is_scanning:
            return

        self.is_scanning = True
        self.btn_scan.configure(state="disabled", text=t("dash_btn_scanning"))
        self.prog_bar.pack(fill="x", padx=20, pady=(0, 15), before=self.card_crit.master)
        self.prog_bar.start()

        def _worker():
            try:
                summary = self.health_suite.run_full_scan(deep_mesh_scan=True)
            except Exception as e:
                summary = {"error": str(e)}

            self.after(0, lambda: self._on_scan_completed(summary))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_scan_completed(self, summary):
        self.last_summary = summary
        self.is_scanning = False
        self.btn_scan.configure(state="normal", text=t("dash_btn_scan"))
        self.prog_bar.stop()
        self.prog_bar.pack_forget()

        if "error" in summary:
            messagebox.showerror(t("dash_dialog_scan_error_title"), t("dash_dialog_scan_error_msg", error=summary['error']))
            return

        # Update Score & Badges
        score = summary["health_score"]
        self.lbl_score.configure(text=str(score))
        status = summary["health_status"]

        if status == "Healthy Green":
            color = COLOR_HEALTHY
            status_text = t("dash_status_healthy")
        elif status == "Warning Yellow":
            color = COLOR_WARNING
            status_text = t("dash_status_warning")
        else:
            color = COLOR_CRITICAL
            status_text = t("dash_status_critical")

        self.lbl_score.configure(text_color=color)
        self.lbl_status_badge.configure(text=status_text.upper(), text_color=color)
        scan_time = summary.get('last_scan_time', 'Just now')
        self.lbl_last_scan.configure(text=t("dash_last_scan_time", time=scan_time))

        # Update Cards
        crit_c = summary["critical_count"]
        warn_c = summary["warning_count"]
        self.card_crit.lbl_count.configure(text=str(crit_c))
        self.card_warn.lbl_count.configure(text=str(warn_c))
        self.card_healthy.lbl_count.configure(
            text=t("dash_card_healthy_optimal") if crit_c == 0 and warn_c == 0 else f"{score}%",
            text_color=COLOR_HEALTHY if score >= 85 else COLOR_WARNING
        )

        self.lbl_issue_count.configure(text=t("dash_issues_detected", count=summary['total_issues']))

        # Render Issues List
        for w in self.issues_list_frame.winfo_children():
            w.destroy()

        if not summary["issues"]:
            clean_box = ctk.CTkFrame(self.issues_list_frame, fg_color="#064E3B", corner_radius=8)
            clean_box.pack(fill="x", pady=10)
            ctk.CTkLabel(
                clean_box,
                text=t("dash_all_clean"),
                font=get_font(13, "bold"), text_color=COLOR_HEALTHY
            ).pack(pady=20)
            return

        for issue in summary["issues"]:
            row = ctk.CTkFrame(self.issues_list_frame, fg_color="#0A111E", corner_radius=8, border_width=1, border_color=BORDER_COLOR)
            row.pack(fill="x", pady=4)

            if issue.severity == "CRITICAL":
                badge_bg = COLOR_CRITICAL_BG
                badge_fg = "#FCA5A5"
            else:
                badge_bg = COLOR_WARNING_BG
                badge_fg = "#FDE047"

            badge = ctk.CTkLabel(
                row, text=f" {issue.severity} ",
                font=get_font(10, "bold"),
                fg_color=badge_bg, text_color=badge_fg, corner_radius=4
            )
            badge.pack(side="left", padx=(12, 10), pady=12)

            text_col = ctk.CTkFrame(row, fg_color="transparent")
            text_col.pack(side="left", fill="both", expand=True, pady=8)

            ctk.CTkLabel(
                text_col, text=f"[{issue.category}] {issue.title}",
                font=get_font(12, "bold"), text_color=TEXT_PRIMARY
            ).pack(anchor="w")

            ctk.CTkLabel(
                text_col, text=issue.description,
                font=get_font(11), text_color=TEXT_SECONDARY,
                wraplength=600, justify="left"
            ).pack(anchor="w")

            if issue.auto_fixable:
                ctk.CTkLabel(
                    row, text=t("dash_autofixable_tag"),
                    font=get_font(10, "bold"), text_color=COLOR_HEALTHY
                ).pack(side="right", padx=15)

    def start_auto_fix(self):
        if self.is_scanning:
            return

        confirm = messagebox.askyesno(
            t("dash_dialog_autofix_title"),
            t("dash_dialog_autofix_confirm")
        )
        if not confirm:
            return

        self.btn_autofix.configure(state="disabled", text=t("dash_btn_fixing"))
        self.prog_bar.pack(fill="x", padx=20, pady=(0, 15), before=self.card_crit.master)
        self.prog_bar.start()

        def _worker():
            try:
                res = self.health_suite.execute_auto_fix_all()
            except Exception as e:
                res = {"error": str(e)}

            self.after(0, lambda: self._on_autofix_completed(res))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_autofix_completed(self, res):
        self.btn_autofix.configure(state="normal", text=t("dash_btn_autofix"))
        self.prog_bar.stop()
        self.prog_bar.pack_forget()

        if "error" in res:
            messagebox.showerror(t("dash_dialog_autofix_err_title"), t("dash_dialog_autofix_err_msg", error=res['error']))
            return

        summary = self.health_suite.get_summary()
        self._on_scan_completed(summary)

        actions_str = "\n• " + "\n• ".join(res["actions_taken"]) if res["actions_taken"] else "None needed."
        messagebox.showinfo(
            t("dash_dialog_autofix_done_title"),
            t(
                "dash_dialog_autofix_done_msg",
                initial_score=res['initial_score'],
                new_score=res['new_score'],
                new_status=res['new_status'],
                actions_count=res['actions_count'],
                actions_str=actions_str,
                quarantine_dir=res['quarantine_dir']
            )
        )

    def update_ui_language(self):
        """Dynamically re-applies translations to all labels, cards, and buttons."""
        self.lbl_score_header.configure(text=t("dash_score_title"))
        self.lbl_main_title.configure(text=t("dash_title"))
        self.lbl_main_desc.configure(text=t("dash_desc"))

        if not self.is_scanning:
            self.btn_scan.configure(text=t("dash_btn_scan"))
        self.btn_autofix.configure(text=t("dash_btn_autofix"))

        self.card_crit.lbl_title.configure(text=t("dash_card_crit_title"))
        self.card_crit.lbl_desc.configure(text=t("dash_card_crit_desc"))
        self.card_warn.lbl_title.configure(text=t("dash_card_warn_title"))
        self.card_warn.lbl_desc.configure(text=t("dash_card_warn_desc"))
        self.card_healthy.lbl_title.configure(text=t("dash_card_healthy_title"))
        self.card_healthy.lbl_desc.configure(text=t("dash_card_healthy_desc"))

        self.lbl_findings_header.configure(text=t("dash_log_title"))

        if hasattr(self, "last_summary") and self.last_summary:
            self._on_scan_completed(self.last_summary)
        else:
            self.lbl_last_scan.configure(text=t("dash_last_scan_never"))
            self.lbl_status_badge.configure(text=t("dash_status_healthy"))
            self.card_healthy.lbl_count.configure(text=t("dash_card_healthy_optimal"))
            self.lbl_issue_count.configure(text=t("dash_issues_count", count=0))
            self._render_empty_state()
