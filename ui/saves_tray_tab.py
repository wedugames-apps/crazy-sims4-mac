"""
==============================================================================
Crazy The Sims 4 Project - Saves & Tray Tab
==============================================================================
Manages:
- Save Game Slots & 1-Click Rollback to EA .ver0
- Point-in-time Snapshot Checkpoints
- Tray Library & CC Dependency Inspector (Detect missing CC, export bundle)
"""

import os
import threading
from tkinter import messagebox, simpledialog, filedialog
import customtkinter as ctk

from ui.theme import (
    BG_CARD, BORDER_COLOR, NEON_CYAN, ELECTRIC_BLUE,
    COLOR_HEALTHY, COLOR_WARNING, COLOR_CRITICAL,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, get_font, format_bytes, neon_btn
)
from diagnostics.health_suite import MasterHealthSuite
from core.archivist import SaveArchivist
from core.tray import TrayInspector
from core.i18n import t


class SavesTrayTab(ctk.CTkFrame):
    """Save game snapshots, 1-Click rollback, and Tray CC inspector."""

    def __init__(self, master, health_suite: MasterHealthSuite):
        super().__init__(master, fg_color="transparent")
        self.health_suite = health_suite
        self.saves_dir = health_suite.saves_folder
        self.tray_dir = os.path.join(health_suite.ts4_user_folder, "Tray") if health_suite.ts4_user_folder else ""
        self.mods_dir = health_suite.mods_folder

        self.archivist = SaveArchivist(self.saves_dir) if self.saves_dir else None
        self.tray_inspector = TrayInspector(self.tray_dir, self.mods_dir) if self.tray_dir else None
        self._scanned_items = None

        self._build_ui()
        self.refresh_saves()

    def _build_ui(self):
        self.scroll = ctk.CTkScrollableFrame(self, fg_color="transparent")
        self.scroll.pack(fill="both", expand=True, padx=20, pady=15)

        # 1. Save Game Archivist & Rollback Section
        sec_saves = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        sec_saves.pack(fill="x", pady=(0, 15))

        sv_head = ctk.CTkFrame(sec_saves, fg_color="transparent")
        sv_head.pack(fill="x", padx=20, pady=(15, 10))

        self.lbl_saves_title = ctk.CTkLabel(
            sv_head, text=t("saves_sec_saves_title"),
            font=get_font(14, "bold"), text_color=NEON_CYAN
        )
        self.lbl_saves_title.pack(side="left")

        btn_box = ctk.CTkFrame(sv_head, fg_color="transparent")
        btn_box.pack(side="right")

        self.btn_snapshot = neon_btn(
            btn_box, text=t("saves_btn_snapshot"),
            command=self.create_snapshot_dialog,
            style="blue",
            width=160, height=32
        )
        self.btn_snapshot.pack(side="left", padx=(0, 8))

        self.btn_purge_ver = neon_btn(
            btn_box, text=t("saves_btn_purge_ver"),
            command=self.purge_ver_backups,
            style="secondary",
            width=180, height=32
        )
        self.btn_purge_ver.pack(side="left")

        # Save Slot List Box
        self.saves_list_frame = ctk.CTkFrame(sec_saves, fg_color="transparent")
        self.saves_list_frame.pack(fill="x", padx=20, pady=(0, 15))

        # 2. Tray Library & CC Inspector Section
        sec_tray = ctk.CTkFrame(self.scroll, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        sec_tray.pack(fill="x")

        tr_head = ctk.CTkFrame(sec_tray, fg_color="transparent")
        tr_head.pack(fill="x", padx=20, pady=(15, 10))

        self.lbl_tray_title = ctk.CTkLabel(
            tr_head, text=t("saves_sec_tray_title"),
            font=get_font(14, "bold"), text_color=COLOR_HEALTHY
        )
        self.lbl_tray_title.pack(side="left")

        tr_btn_box = ctk.CTkFrame(tr_head, fg_color="transparent")
        tr_btn_box.pack(side="right")

        self.btn_scan_tray = neon_btn(
            tr_btn_box, text=t("saves_btn_scan_tray"),
            command=self.scan_tray,
            style="green",
            width=160, height=32
        )
        self.btn_scan_tray.pack(side="left", padx=(0, 8))

        self.btn_export_bundle = neon_btn(
            tr_btn_box, text=t("saves_btn_export_bundle"),
            command=self.export_tray_bundle_dialog,
            style="blue",
            width=190, height=32
        )
        self.btn_export_bundle.pack(side="left")

        self.lbl_tray_status = ctk.CTkLabel(
            sec_tray,
            text=t("saves_tray_desc"),
            font=get_font(11), text_color=TEXT_SECONDARY
        )
        self.lbl_tray_status.pack(anchor="w", padx=20, pady=(0, 10))

        self.txt_tray_results = ctk.CTkTextbox(
            sec_tray, height=120, fg_color="#0A111E",
            font=get_font(11, family="Consolas"), text_color="#E2E8F0"
        )
        self.txt_tray_results.pack(fill="x", padx=20, pady=(0, 15))
        self.txt_tray_results.insert("1.0", t("saves_tray_placeholder"))
        self.txt_tray_results.configure(state="disabled")

    def refresh_saves(self):
        for w in self.saves_list_frame.winfo_children():
            w.destroy()

        if not self.archivist or not os.path.isdir(self.saves_dir):
            ctk.CTkLabel(
                self.saves_list_frame, text=t("saves_not_found"),
                font=get_font(12), text_color=COLOR_WARNING
            ).pack(anchor="w")
            return

        slots = self.archivist.scan_slots()
        if not slots:
            ctk.CTkLabel(
                self.saves_list_frame, text=t("saves_no_slots"),
                font=get_font(12), text_color=TEXT_MUTED
            ).pack(anchor="w")
            return

        for slot_hex, slot in sorted(slots.items(), key=lambda x: x[1].slot_dec):
            row = ctk.CTkFrame(self.saves_list_frame, fg_color="#0A111E", corner_radius=8, border_width=1, border_color=BORDER_COLOR)
            row.pack(fill="x", pady=4)

            # Slot icon / tag
            name_str = t("saves_slot_label", dec=slot.slot_dec, hex=slot.slot_hex)
            if slot.is_autosave:
                name_str += t("saves_slot_autosave")

            color = COLOR_CRITICAL if slot.is_corrupted else COLOR_HEALTHY
            status_text = t("saves_status_corrupted") if slot.is_corrupted else t("saves_status_healthy")

            ctk.CTkLabel(
                row, text=f" {status_text} ",
                font=get_font(10, "bold"), fg_color=color, text_color="#FFFFFF", corner_radius=4
            ).pack(side="left", padx=(12, 10), pady=10)

            info_box = ctk.CTkFrame(row, fg_color="transparent")
            info_box.pack(side="left", fill="both", expand=True, pady=6)

            ctk.CTkLabel(
                info_box, text=name_str, font=get_font(12, "bold"), text_color=TEXT_PRIMARY
            ).pack(anchor="w")

            detail_str = t(
                "saves_slot_details",
                size=format_bytes(slot.total_size),
                last_played=slot.last_played_str,
                ver_count=len(slot.versions)
            )
            ctk.CTkLabel(
                info_box, text=detail_str, font=get_font(10), text_color=TEXT_SECONDARY
            ).pack(anchor="w")

            # Rollback button (if backups exist)
            if slot.versions:
                btn_rb = neon_btn(
                    row, text=t("saves_btn_rollback"),
                    command=lambda s=slot.slot_hex: self.rollback_slot(s),
                    style="amber",
                    width=150, height=28,
                    font=get_font(11, "bold")
                )
                btn_rb.pack(side="right", padx=12)

    def rollback_slot(self, slot_hex: str):
        confirm = messagebox.askyesno(
            t("saves_rollback_confirm_title"),
            t("saves_rollback_confirm_msg", slot=slot_hex)
        )
        if not confirm:
            return

        ok, msg = self.archivist.rollback_slot_to_version(slot_hex, target_ver=0)
        if ok:
            messagebox.showinfo(t("saves_rollback_done_title"), msg)
        else:
            messagebox.showerror(t("saves_rollback_err_title"), msg)
        self.refresh_saves()

    def create_snapshot_dialog(self):
        if not self.archivist:
            return

        label = simpledialog.askstring(t("saves_snapshot_prompt_title"), t("saves_snapshot_prompt_msg"))
        if not label:
            return

        ok, msg = self.archivist.create_snapshot(label=label, notes="User initiated snapshot")
        if ok:
            messagebox.showinfo(t("saves_snapshot_done_title"), t("saves_snapshot_done_msg", msg=msg))
        else:
            messagebox.showerror(t("saves_snapshot_err_title"), msg)

    def purge_ver_backups(self):
        if not self.archivist:
            return

        confirm = messagebox.askyesno(
            t("saves_purge_confirm_title"),
            t("saves_purge_confirm_msg")
        )
        if not confirm:
            return

        deleted, freed = self.archivist.purge_old_versions(keep_latest_ver=True)
        messagebox.showinfo(
            t("saves_purge_done_title"),
            t("saves_purge_done_msg", deleted=deleted, freed=format_bytes(freed))
        )
        self.refresh_saves()

    def scan_tray(self):
        if not self.tray_inspector:
            messagebox.showwarning(t("common_notice"), t("doc_notice_mods_missing"))
            return

        self.txt_tray_results.configure(state="normal")
        self.txt_tray_results.delete("1.0", "end")
        self.txt_tray_results.insert("1.0", t("saves_tray_scanning"))
        self.txt_tray_results.configure(state="disabled")

        def _worker():
            self.tray_inspector.build_mods_index(max_packages=500)
            items = self.tray_inspector.scan_tray_items()
            self.after(0, lambda: self._on_tray_scanned(items))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_tray_scanned(self, items):
        self._scanned_items = items
        self.txt_tray_results.configure(state="normal")
        self.txt_tray_results.delete("1.0", "end")

        if not items:
            self.txt_tray_results.insert("1.0", t("saves_tray_none_found"))
            self.txt_tray_results.configure(state="disabled")
            return

        out = []
        out.append(t("saves_tray_scanned_header", count=len(items)))

        for item in items[:15]:
            dep = self.tray_inspector.check_item_dependencies(item)
            out.append(f"• [{item.item_type}] {item.name}")
            if item.creator_name:
                out.append(t("saves_tray_creator", creator=item.creator_name))
            out.append(t("saves_tray_found_cc", count=dep['found_cc_count']))
            if dep["missing_instance_count"] > 0:
                out.append(t("saves_tray_missing_cc", count=dep['missing_instance_count']))
            out.append("")

        self.txt_tray_results.insert("1.0", "\n".join(out))
        self.txt_tray_results.configure(state="disabled")
        self.lbl_tray_status.configure(text=t("saves_tray_status_done", count=len(items)))

    def export_tray_bundle_dialog(self):
        items = getattr(self, "_scanned_items", None)
        if not items:
            messagebox.showinfo(t("saves_export_bundle_title"), t("saves_export_bundle_first_scan"))
            return

        target_item = items[0]
        out_zip = filedialog.asksaveasfilename(
            title=t("saves_export_bundle_dialog_title", name=target_item.name),
            defaultextension=".zip",
            filetypes=[("ZIP Archive", "*.zip")],
            initialfile=f"{target_item.name}_Bundle.zip"
        )
        if not out_zip:
            return

        ok = self.tray_inspector.export_tray_bundle(target_item, out_zip)
        if ok:
            messagebox.showinfo(
                t("saves_export_bundle_done_title"),
                t("saves_export_bundle_done_msg", name=target_item.name, path=out_zip)
            )
        else:
            messagebox.showerror(t("saves_export_bundle_err_title"), t("saves_export_bundle_err_msg"))

    def update_ui_language(self):
        """Dynamically re-applies translations to all labels and buttons."""
        self.lbl_saves_title.configure(text=t("saves_sec_saves_title"))
        self.btn_snapshot.configure(text=t("saves_btn_snapshot"))
        self.btn_purge_ver.configure(text=t("saves_btn_purge_ver"))

        self.lbl_tray_title.configure(text=t("saves_sec_tray_title"))
        self.btn_scan_tray.configure(text=t("saves_btn_scan_tray"))
        self.btn_export_bundle.configure(text=t("saves_btn_export_bundle"))
        if self._scanned_items is not None:
            self.lbl_tray_status.configure(text=t("saves_tray_status_done", count=len(self._scanned_items)))
        else:
            self.lbl_tray_status.configure(text=t("saves_tray_desc"))
            self.txt_tray_results.configure(state="normal")
            self.txt_tray_results.delete("1.0", "end")
            self.txt_tray_results.insert("1.0", t("saves_tray_placeholder"))
            self.txt_tray_results.configure(state="disabled")

        self.refresh_saves()
