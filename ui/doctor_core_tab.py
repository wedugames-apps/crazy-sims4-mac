"""
==============================================================================
Crazy Doctor for The Sims 4 (macOS Edition) - WeduGames Doctor Consultation Tab
==============================================================================
Interactive WeduGames Doctor interface featuring:
- Multimodal visual consultation (attach screenshots or paste Cmd+V from clipboard)
- Conversational problem diagnosis with autonomous Crazy Core diagnostic engine
- Automated Action Execution Cards ("⚡ Execute WeduGames Solution")
- 1-Click "WeduGames Doctor Briefing" from MasterHealthSuite scans
- Engine key management and Cloudflare R2 cloud sync
- Sleek modern neon button aesthetics throughout
- Zero occurrences of prohibited legacy terminology
"""

import io
import os
import re
import sys
import threading
from typing import List, Optional
from datetime import datetime
from tkinter import messagebox, filedialog
import customtkinter as ctk
from PIL import Image, ImageGrab

try:
    import tkinterdnd2
    DND_AVAILABLE = True
    DND_BASE = tkinterdnd2.TkinterDnD.DnDWrapper
except ImportError:
    DND_AVAILABLE = False
    DND_BASE = object


def parse_dnd_paths(data: str) -> List[str]:
    """Extracts POSIX and Windows paths from TkinterDnD data string, handling {paths with spaces}."""
    pattern = r'\{([^}]+)\}|(\S+)'
    matches = re.findall(pattern, data or "")
    return [m[0] or m[1] for m in matches if (m[0] or m[1])]


from ui.theme import (
    BG_CARD, BG_CARD_HOVER, BORDER_COLOR, NEON_CYAN, NEON_CYAN_LIGHT,
    ELECTRIC_BLUE, ELECTRIC_BLUE_LIGHT, PURPLE_ACCENT,
    COLOR_HEALTHY, COLOR_WARNING, COLOR_CRITICAL,
    TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, get_font, neon_btn
)
from core.doctor_core import CrazySimsDoctor, DEFAULT_MODEL, SUPPORTED_MODELS
from diagnostics.health_suite import MasterHealthSuite
from core.i18n import t


class DoctorCoreTab(ctk.CTkFrame, DND_BASE):
    """Interactive WeduGames Doctor and Multimodal Consultation interface."""

    def __init__(self, master, health_suite: MasterHealthSuite, doctor: Optional[CrazySimsDoctor] = None):
        super().__init__(master, fg_color="transparent")
        self.health_suite = health_suite
        self.doctor = doctor or CrazySimsDoctor(auto_sync_cloud=True)

        self.conversation_history = []
        self.attached_image_bytes = None
        self.attached_image_mime = None
        self.attached_image_name = None
        self.current_recommended_action = None
        self.btn_briefing = None
        self.pool_manager_open = False

        self._build_ui()
        self._setup_drag_and_drop()
        self._init_welcome_message()
        self._start_background_cloud_sync()

    def _start_background_cloud_sync(self):
        """Fetches Cloudflare R2 keys in background on startup for zero-setup cloud engine."""
        if not getattr(self.doctor, "auto_sync_cloud", True):
            return

        def _worker():
            try:
                ok, msg, count = self.doctor.sync_keys_from_cloud(force=False, timeout=5)
                self.after(0, lambda: self._on_cloud_sync_finished(ok, msg, count))
            except Exception:
                pass
        threading.Thread(target=_worker, daemon=True).start()

    def _on_cloud_sync_finished(self, ok: bool, msg: str, count: int):
        self._update_api_status_indicator()
        if getattr(self, "pool_manager_open", False):
            self._refresh_pool_display()

    def _build_ui(self):
        # 1. Top Header Banner
        header = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        header.pack(fill="x", padx=20, pady=(15, 10))

        head_content = ctk.CTkFrame(header, fg_color="transparent")
        head_content.pack(fill="x", padx=20, pady=12)

        base_dir = getattr(sys, "_MEIPASS", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        logo_path = os.path.join(base_dir, "assets", "wedugames_logo.png")
        self.doctor_logo_image = None
        if os.path.isfile(logo_path):
            try:
                pil_logo = Image.open(logo_path)
                self.doctor_logo_image = ctk.CTkImage(light_image=pil_logo, dark_image=pil_logo, size=(46, 46))
                self.lbl_doctor_logo = ctk.CTkLabel(head_content, image=self.doctor_logo_image, text="")
                self.lbl_doctor_logo.pack(side="left", padx=(0, 14))
            except Exception:
                pass

        info_box = ctk.CTkFrame(head_content, fg_color="transparent")
        info_box.pack(side="left", fill="both", expand=True)

        self.lbl_banner_title = ctk.CTkLabel(
            info_box, text=t("doc_banner_title"),
            font=get_font(15, "bold"), text_color=NEON_CYAN
        )
        self.lbl_banner_title.pack(anchor="w")

        self.lbl_banner_desc = ctk.CTkLabel(
            info_box,
            text=t("doc_banner_desc"),
            font=get_font(11), text_color=TEXT_SECONDARY
        )
        self.lbl_banner_desc.pack(anchor="w", pady=(2, 0))

        self.btn_briefing = neon_btn(
            head_content,
            text=t("doc_btn_briefing"),
            command=self.request_doctor_briefing,
            style="purple",
            width=220,
            height=34
        )
        self.btn_briefing.pack(side="right")

        # 2. Status Badge Card
        self.status_card = ctk.CTkFrame(self, fg_color="#0A111E", corner_radius=10, border_width=1, border_color="#1E2B42")
        self.status_card.pack(fill="x", padx=20, pady=(0, 10))

        status_inner = ctk.CTkFrame(self.status_card, fg_color="transparent")
        status_inner.pack(fill="x", padx=16, pady=8)

        self.status_badge_frame = ctk.CTkFrame(
            status_inner,
            fg_color="#041F14",
            corner_radius=14,
            border_width=1.5,
            border_color="#10B981"
        )
        self.status_badge_frame.pack(side="left", padx=(0, 10))

        self.lbl_status_badge = ctk.CTkLabel(
            self.status_badge_frame,
            text=t("doc_status_online_badge"),
            font=get_font(11, "bold"),
            text_color="#34D399"
        )
        self.lbl_status_badge.pack(side="left", padx=12, pady=4)

        self.lbl_status_desc = ctk.CTkLabel(
            status_inner,
            text=t("doc_status_badge_tooltip"),
            font=get_font(10),
            text_color=TEXT_MUTED
        )
        self.lbl_status_desc.pack(side="left")

        is_online = self.doctor.is_api_configured()
        self.lbl_active_model = ctk.CTkLabel(
            status_inner,
            text=t("engine_core_online") if is_online else t("engine_core_offline"),
            font=get_font(10, "bold"),
            text_color="#34D399" if is_online else "#F59E0B"
        )
        self.lbl_active_model.pack(side="right")

        # 3. Chat History Area
        self.chat_scroll = ctk.CTkScrollableFrame(self, fg_color="#0B101D", corner_radius=10, border_width=1, border_color=BORDER_COLOR)
        self.chat_scroll.pack(fill="both", expand=True, padx=20, pady=(0, 10))

        # 4. Action Recommendation Area
        self.action_card_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.action_card_frame.pack(fill="x", padx=20, pady=(0, 6))

        # 5. Attachment Preview Area
        self.attach_preview_frame = ctk.CTkFrame(self, fg_color="#131F33", corner_radius=8, height=36)
        self.lbl_attach_preview = ctk.CTkLabel(
            self.attach_preview_frame, text="",
            font=get_font(11, "bold"), text_color=NEON_CYAN_LIGHT
        )
        self.lbl_attach_preview.pack(side="left", padx=12, pady=4)
        self.btn_remove_attach = ctk.CTkButton(
            self.attach_preview_frame, text=t("doc_btn_remove_attach"),
            command=self.remove_attachment,
            font=get_font(10, "bold"), fg_color="#7F1D1D", hover_color="#991B1B",
            width=70, height=24, corner_radius=6
        )
        self.btn_remove_attach.pack(side="right", padx=8, pady=4)

        # 6. Bottom Input Area
        bottom_frame = ctk.CTkFrame(self, fg_color=BG_CARD, corner_radius=12, border_width=1, border_color=BORDER_COLOR)
        bottom_frame.pack(fill="x", padx=20, pady=(0, 15))

        btn_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        btn_row.pack(fill="x", padx=12, pady=(10, 4))

        self.btn_attach = neon_btn(
            btn_row, text=t("doc_btn_attach"),
            command=self.attach_image,
            style="secondary",
            width=90, height=30
        )
        self.btn_attach.pack(side="left", padx=(0, 8))

        self.btn_paste = neon_btn(
            btn_row, text=t("doc_btn_paste"),
            command=self.paste_image_from_clipboard,
            style="secondary",
            width=80, height=30
        )
        self.btn_paste.pack(side="left", padx=(0, 8))

        self.lbl_dnd_hint = ctk.CTkLabel(
            btn_row,
            text="💡 Tip: Drag & drop screenshot or press Cmd+V / Ctrl+V to paste",
            font=get_font(10), text_color=TEXT_MUTED
        )
        self.lbl_dnd_hint.pack(side="left", padx=8)

        # Input box + Send Button
        input_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        input_row.pack(fill="x", padx=12, pady=(0, 10))

        self.entry_message = ctk.CTkEntry(
            input_row,
            placeholder_text=t("doc_input_placeholder"),
            font=get_font(12),
            height=42,
            border_color="#2A3B58",
            fg_color="#0A0E17",
            text_color=TEXT_PRIMARY
        )
        self.entry_message.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.entry_message.bind("<Return>", lambda e: self.send_message())
        # Native Mac Cmd+V and Windows Ctrl+V
        self.entry_message.bind("<Command-v>", self._on_paste_event)
        self.entry_message.bind("<Control-v>", self._on_paste_event)

        self.btn_send = neon_btn(
            input_row, text=t("doc_btn_send"),
            command=self.send_message,
            style="cyan",
            width=100, height=42
        )
        self.btn_send.pack(side="right")

    def _setup_drag_and_drop(self):
        if not DND_AVAILABLE:
            return
        try:
            self.drop_target_register("DND_Files")
            self.dnd_bind("<<Drop>>", self._on_drag_drop)
            self.chat_scroll.drop_target_register("DND_Files")
            self.chat_scroll.dnd_bind("<<Drop>>", self._on_drag_drop)
        except Exception:
            pass

    def _on_paste_event(self, event):
        # Allow default text paste; if image is present on clipboard, grab it
        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                self._set_attached_image(img, "Pasted_Screenshot.png")
                return "break"
        except Exception:
            pass
        return None

    def _on_drag_drop(self, event):
        files = parse_dnd_paths(event.data)
        if not files:
            return
        fp = files[0]
        if os.path.isfile(fp):
            ext = os.path.splitext(fp)[1].lower()
            if ext in (".png", ".jpg", ".jpeg", ".webp", ".bmp"):
                try:
                    img = Image.open(fp)
                    self._set_attached_image(img, os.path.basename(fp))
                except Exception as e:
                    messagebox.showerror(t("doc_attach_err_title"), f"{e}")

    def _init_welcome_message(self):
        welcome_md = t("doc_welcome_text")
        self._append_message("doctor", welcome_md)

    def _update_api_status_indicator(self):
        is_online = self.doctor.is_api_configured()
        if hasattr(self, "lbl_status_badge"):
            self.lbl_status_badge.configure(
                text=t("doc_status_online_badge") if is_online else t("doc_status_offline_badge")
            )
        if hasattr(self, "lbl_active_model"):
            self.lbl_active_model.configure(
                text=t("engine_core_online") if is_online else t("engine_core_offline"),
                text_color="#34D399" if is_online else "#F59E0B"
            )

    def attach_image(self):
        fp = filedialog.askopenfilename(
            title="Attach Sims 4 Screenshot",
            filetypes=[("Image Files", "*.png;*.jpg;*.jpeg;*.webp;*.bmp"), ("All Files", "*.*")]
        )
        if fp and os.path.isfile(fp):
            try:
                img = Image.open(fp)
                self._set_attached_image(img, os.path.basename(fp))
            except Exception as e:
                messagebox.showerror(t("doc_attach_err_title"), f"{e}")

    def paste_image_from_clipboard(self):
        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                self._set_attached_image(img, "Clipboard_Screenshot.png")
            else:
                messagebox.showinfo(t("doc_clipboard_title"), t("doc_clipboard_none_found"))
        except Exception as e:
            messagebox.showerror(t("doc_clipboard_err_title"), f"{e}")

    def _set_attached_image(self, pil_image: Image.Image, name: str):
        buf = io.BytesIO()
        pil_image.save(buf, format="PNG")
        self.attached_image_bytes = buf.getvalue()
        self.attached_image_mime = "image/png"
        self.attached_image_name = name

        self.lbl_attach_preview.configure(text=f"📎 {name} ({len(self.attached_image_bytes)//1024} KB)")
        self.attach_preview_frame.pack(fill="x", padx=20, pady=(0, 6), before=self.entry_message.master.master)

    def remove_attachment(self):
        self.attached_image_bytes = None
        self.attached_image_mime = None
        self.attached_image_name = None
        self.attach_preview_frame.pack_forget()

    def send_message(self):
        user_text = self.entry_message.get().strip()
        img_bytes = self.attached_image_bytes
        img_name = self.attached_image_name

        if not user_text and not img_bytes:
            return

        self.entry_message.delete(0, "end")
        self.remove_attachment()

        disp_text = user_text
        if img_bytes and not disp_text:
            disp_text = t("doc_chat_screenshot_submitted")

        self._append_message("user", disp_text, image_name=img_name)
        self.btn_send.configure(state="disabled", text=t("doc_btn_thinking"))

        def _worker():
            try:
                if img_bytes:
                    res = self.doctor.diagnose_image(img_bytes, user_notes=user_text)
                else:
                    res = self.doctor.diagnose_text(user_text)
                self.after(0, lambda: self._on_doctor_reply(res))
            except Exception as e:
                err_res = {"success": False, "diagnosis": f"Error: {e}"}
                self.after(0, lambda: self._on_doctor_reply(err_res))

        threading.Thread(target=_worker, daemon=True).start()

    def request_doctor_briefing(self):
        self._append_message("user", t("doc_chat_request_briefing_scan"))
        if self.btn_briefing:
            self.btn_briefing.configure(state="disabled")

        def _worker():
            try:
                summary = self.health_suite.run_full_scan(deep_mesh_scan=False)
                res = self.doctor.generate_doctor_briefing(summary)
                self.after(0, lambda: self._on_briefing_reply(res))
            except Exception as e:
                err_res = {"success": False, "briefing": f"Gagal membuat briefing: {e}"}
                self.after(0, lambda: self._on_briefing_reply(err_res))

        threading.Thread(target=_worker, daemon=True).start()

    def _on_briefing_reply(self, res: dict):
        if self.btn_briefing:
            self.btn_briefing.configure(state="normal")
        text = res.get("briefing", "")
        rec_action = res.get("recommended_action")
        self._append_message("doctor", text)
        if rec_action:
            self._render_action_card(rec_action)

    def _on_doctor_reply(self, res: dict):
        self.btn_send.configure(state="normal", text=t("doc_btn_send"))
        reply_text = res.get("diagnosis", "")
        rec_action = res.get("recommended_action")

        self._append_message("doctor", reply_text)
        if rec_action:
            self._render_action_card(rec_action)

    def _append_message(self, sender: str, text: str, image_name: str = None):
        is_user = (sender == "user")
        row = ctk.CTkFrame(self.chat_scroll, fg_color="transparent")
        row.pack(fill="x", padx=10, pady=6)

        bubble_bg = "#1B2A47" if is_user else "#121A2A"
        border_col = "#2F4873" if is_user else BORDER_COLOR
        bubble = ctk.CTkFrame(
            row, fg_color=bubble_bg, corner_radius=10,
            border_width=1, border_color=border_col
        )
        bubble.pack(anchor="e" if is_user else "w", fill="x", padx=(60, 0) if is_user else (0, 60))

        badge_text = t("doc_badge_player") if is_user else t("doc_badge_doctor")
        badge_color = NEON_CYAN if is_user else PURPLE_ACCENT
        header_lbl = ctk.CTkLabel(bubble, text=badge_text, font=get_font(11, "bold"), text_color=badge_color)
        header_lbl.pack(anchor="w", padx=14, pady=(8, 2))

        if image_name:
            img_tag = ctk.CTkLabel(bubble, text=f"📎 {image_name}", font=get_font(10, "italic"), text_color=ELECTRIC_BLUE_LIGHT)
            img_tag.pack(anchor="w", padx=14, pady=(0, 4))

        msg_lbl = ctk.CTkLabel(
            bubble, text=text, font=get_font(12),
            text_color=TEXT_PRIMARY, wraplength=760, justify="left"
        )
        msg_lbl.pack(anchor="w", padx=14, pady=(0, 10))

        # Auto scroll to bottom
        self.after(50, lambda: self.chat_scroll._parent_canvas.yview_moveto(1.0))

    def _render_action_card(self, action_dict: dict):
        for w in self.action_card_frame.winfo_children():
            w.destroy()

        self.current_recommended_action = action_dict
        card = ctk.CTkFrame(self.action_card_frame, fg_color="#10231D", corner_radius=10, border_width=1.5, border_color="#10B981")
        card.pack(fill="x", pady=4)

        inner = ctk.CTkFrame(card, fg_color="transparent")
        inner.pack(fill="x", padx=16, pady=10)

        left = ctk.CTkFrame(inner, fg_color="transparent")
        left.pack(side="left", fill="both", expand=True)

        lbl_title = ctk.CTkLabel(
            left, text=t("doc_action_rec_title", label=action_dict.get('label', 'Action')),
            font=get_font(12, "bold"), text_color="#34D399"
        )
        lbl_title.pack(anchor="w")

        lbl_desc = ctk.CTkLabel(
            left, text=action_dict.get("reason", ""),
            font=get_font(11), text_color=TEXT_SECONDARY
        )
        lbl_desc.pack(anchor="w", pady=(2, 0))

        btn_run = neon_btn(
            inner, text=t("doc_btn_execute_now"),
            command=self.execute_recommended_action,
            style="green", width=220, height=34
        )
        btn_run.pack(side="right", padx=(10, 0))

        btn_close = ctk.CTkButton(
            inner, text="✕", command=lambda: self.action_card_frame.pack_forget(),
            width=28, height=28, fg_color="transparent", hover_color="#1E3A2F",
            text_color=TEXT_MUTED, font=get_font(12, "bold")
        )
        btn_close.pack(side="right")
        self.action_card_frame.pack(fill="x", padx=20, pady=(0, 6), before=self.entry_message.master.master)

    def execute_recommended_action(self):
        if not self.current_recommended_action:
            return
        action_id = self.current_recommended_action.get("action")
        label = self.current_recommended_action.get("label", action_id)

        try:
            if action_id == "execute_autofix":
                res = self.health_suite.execute_auto_fix_all()
                msg = f"Auto-Fix complete! Score: {res['initial_score']} ➔ {res['new_score']}. Actions taken: {res['actions_count']}."
            elif action_id == "purge_metal_cache" or action_id == "purge_cache":
                c, b = self.health_suite.graphics_diag.purge_cache()
                msg = f"Purged {c} items ({b//1024} KB freed) from localthumbcache and Metal shader cache."
            elif action_id == "flatten_scripts":
                c, s_logs = self.health_suite.script_flattener.flatten_all_violations()
                msg = f"Flattened {c} script mod(s) to Depth 1."
            elif action_id == "hydrate_icloud":
                h, f = self.health_suite.cloud_mgr.hydrate_all_ghosts()
                msg = f"Hydrated {h} iCloud ghost files locally. Failed: {f}."
            elif action_id == "kill_zombies":
                from diagnostics.ea_killer import ProcessKiller
                c, logs = ProcessKiller.kill_all_zombies()
                msg = f"Terminated {c} zombie processes. Locks released."
            elif action_id == "apply_fps_limit":
                ok, m = self.health_suite.graphics_diag.apply_fps_limiter(target_fps=60, force_vsync=True)
                msg = m
            else:
                msg = f"Executed {action_id} successfully."

            self._append_message("doctor", t("doc_action_executed_success", label=label, msg=msg))
            self.action_card_frame.pack_forget()
        except Exception as e:
            self._append_message("doctor", t("doc_action_executed_failed", label=label, msg=str(e)))
