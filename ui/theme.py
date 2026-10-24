"""
==============================================================================
Crazy Doctor for The Sims 4 (macOS Edition) - UI Theme & Style Configuration
==============================================================================
Modern Neon Dark Cyberpunk palette tailored for macOS with Apple typography
(SF Pro Text / Helvetica Neue) and high-DPI Retina contrast.
"""

import sys
import ctypes
import customtkinter as ctk

# Color Palette
BG_DARK = "#0A0E17"
BG_CARD = "#121A2A"
BG_CARD_HOVER = "#1B263B"
BG_SIDEBAR = "#0E1524"
BG_HEADER = "#0F1829"
BORDER_COLOR = "#1F2B42"

# Neon Accents
NEON_CYAN = "#06B6D4"
NEON_CYAN_LIGHT = "#22D3EE"
ELECTRIC_BLUE = "#3B82F6"
ELECTRIC_BLUE_LIGHT = "#60A5FA"
PURPLE_ACCENT = "#8B5CF6"
PURPLE_LIGHT = "#C084FC"

# Status Badges
COLOR_HEALTHY = "#10B981"      # Emerald Green
COLOR_HEALTHY_BG = "#064E3B"
COLOR_WARNING = "#F59E0B"      # Amber Yellow
COLOR_WARNING_BG = "#78350F"
COLOR_CRITICAL = "#EF4444"     # Crimson Red
COLOR_CRITICAL_BG = "#7F1D1D"

# Text Colors
TEXT_PRIMARY = "#F8FAFC"
TEXT_SECONDARY = "#94A3B8"
TEXT_MUTED = "#64748B"

# Modern Neon Button Styles
NEON_BTN_CYAN = {
    "fg_color": "#0B1626",
    "border_color": "#06B6D4",
    "border_width": 1.5,
    "text_color": "#22D3EE",
    "hover_color": "#12253E",
}

NEON_BTN_BLUE = {
    "fg_color": "#0C152B",
    "border_color": "#3B82F6",
    "border_width": 1.5,
    "text_color": "#93C5FD",
    "hover_color": "#132347",
}

NEON_BTN_GREEN = {
    "fg_color": "#081B16",
    "border_color": "#10B981",
    "border_width": 1.5,
    "text_color": "#34D399",
    "hover_color": "#0F2B23",
}

NEON_BTN_AMBER = {
    "fg_color": "#1C1409",
    "border_color": "#F59E0B",
    "border_width": 1.5,
    "text_color": "#FBBF24",
    "hover_color": "#2C200E",
}

NEON_BTN_RED = {
    "fg_color": "#1A0A0E",
    "border_color": "#EF4444",
    "border_width": 1.5,
    "text_color": "#F87171",
    "hover_color": "#2A1218",
}

NEON_BTN_PURPLE = {
    "fg_color": "#140D26",
    "border_color": "#8B5CF6",
    "border_width": 1.5,
    "text_color": "#C4B5FD",
    "hover_color": "#21163E",
}

NEON_BTN_SECONDARY = {
    "fg_color": "#0E1524",
    "border_color": "#27364F",
    "border_width": 1.0,
    "text_color": "#CBD5E1",
    "hover_color": "#18243C",
}


def neon_btn(parent, text: str, command=None, style: str = "cyan", font=None, height=34, width=140, corner_radius=8, **kwargs) -> ctk.CTkButton:
    """Helper to instantiate a standardized neon outlined button."""
    styles = {
        "cyan": NEON_BTN_CYAN,
        "blue": NEON_BTN_BLUE,
        "green": NEON_BTN_GREEN,
        "amber": NEON_BTN_AMBER,
        "yellow": NEON_BTN_AMBER,
        "orange": NEON_BTN_AMBER,
        "red": NEON_BTN_RED,
        "purple": NEON_BTN_PURPLE,
        "magenta": NEON_BTN_PURPLE,
        "violet": NEON_BTN_PURPLE,
        "secondary": NEON_BTN_SECONDARY,
        "gray": NEON_BTN_SECONDARY,
        "grey": NEON_BTN_SECONDARY,
    }
    cfg = dict(styles.get(style, NEON_BTN_CYAN))
    if font is None:
        font = get_font(12, "bold")
    cfg.update({
        "text": text,
        "command": command,
        "font": font,
        "height": height,
        "width": width,
        "corner_radius": corner_radius,
    })
    cfg.update(kwargs)
    return ctk.CTkButton(parent, **cfg)


def get_font(size: int = 13, weight: str = "normal", family: str = None) -> ctk.CTkFont:
    """Returns a standardized CTkFont with native Apple macOS typography fallbacks."""
    if family is None:
        if sys.platform == "darwin":
            family = "SF Pro Text"
        else:
            family = "Segoe UI"
    return ctk.CTkFont(family=family, size=size, weight=weight)


def apply_dark_title_bar(window):
    """Applies native dark window attributes on macOS and Windows."""
    if sys.platform == "darwin":
        # macOS CustomTkinter dark appearance handles dark title bar automatically
        return
    if sys.platform == "win32":
        try:
            window.update_idletasks()
            h = window.winfo_id()
            hwnd = ctypes.windll.user32.GetAncestor(h, 2) or ctypes.windll.user32.GetParent(h) or h
            val_true = ctypes.c_int(1)
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 19, ctypes.byref(val_true), ctypes.sizeof(val_true))
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 20, ctypes.byref(val_true), ctypes.sizeof(val_true))
            caption_color = ctypes.c_int(0x00170E0A)  # BGR order: #0A0E17
            ctypes.windll.dwmapi.DwmSetWindowAttribute(hwnd, 35, ctypes.byref(caption_color), ctypes.sizeof(caption_color))
        except Exception:
            pass


def format_bytes(num: float) -> str:
    """Formats bytes into human readable KB/MB/GB."""
    for unit in ("B", "KB", "MB", "GB"):
        if abs(num) < 1024.0 or unit == "GB":
            return f"{num:.0f} {unit}" if unit == "B" else f"{num:.1f} {unit}"
        num /= 1024.0
    return f"{num:.1f} GB"
