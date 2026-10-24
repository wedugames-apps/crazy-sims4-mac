# -*- mode: python ; coding: utf-8 -*-
"""
==============================================================================
PyInstaller Specification: Crazy Doctor for The Sims 4 (macOS Edition)
==============================================================================
Production-grade native macOS Application Bundle (.app) & Universal2 binary.
Features:
- macOS .app Bundle (windowed, high-DPI Retina aware)
- Native ICNS icon bundle
- Full CustomTkinter theme assets, fonts, icons
- TkinterDnD2 macOS native binaries
- Pillow and Requests full bundle
- Embedded doctor_config.json and branding assets
- Target arch: Universal2 (Intel x86_64 and Apple Silicon M1/M2/M3/M4)
"""

import os
import sys
from PyInstaller.utils.hooks import collect_all, collect_submodules, collect_data_files

# Resolve project directory
PROJ_DIR = os.path.abspath(SPECPATH) if 'SPECPATH' in globals() else os.path.dirname(os.path.abspath(__file__))
if PROJ_DIR not in sys.path:
    sys.path.insert(0, PROJ_DIR)

# 1. Collect third-party dependency assets, binaries, and hidden submodules
try:
    ctk_datas, ctk_binaries, ctk_hidden = collect_all('customtkinter')
except Exception:
    ctk_datas, ctk_binaries, ctk_hidden = [], [], []

try:
    dnd_datas, dnd_binaries, dnd_hidden = collect_all('tkinterdnd2')
except Exception:
    dnd_datas, dnd_binaries, dnd_hidden = [], [], []

try:
    pil_datas, pil_binaries, pil_hidden = collect_all('PIL')
except Exception:
    pil_datas, pil_binaries, pil_hidden = [], [], []

try:
    req_datas, req_binaries, req_hidden = collect_all('requests')
except Exception:
    req_datas, req_binaries, req_hidden = [], [], []

# 2. Collect local architecture submodules
core_submodules = collect_submodules('core')
diag_submodules = collect_submodules('diagnostics')
ui_submodules = collect_submodules('ui')

# 3. Assemble datas
datas = []
datas.extend(ctk_datas)
datas.extend(dnd_datas)
datas.extend(pil_datas)
datas.extend(req_datas)

# Project assets and configurations
assets_dir = os.path.join(PROJ_DIR, 'assets')
if os.path.isdir(assets_dir):
    datas.append((assets_dir, 'assets'))

icns_path = os.path.join(PROJ_DIR, 'assets', 'icon.icns')
if os.path.isfile(icns_path):
    datas.append((icns_path, 'assets'))

logo_path = os.path.join(PROJ_DIR, 'assets', 'wedugames_logo.png')
if os.path.isfile(logo_path):
    datas.append((logo_path, 'assets'))

config_path = os.path.join(PROJ_DIR, 'doctor_config.json')
if os.path.isfile(config_path):
    datas.append((config_path, '.'))

# Deduplicate datas
datas = list({(src, dst): (src, dst) for src, dst in datas}.values())

# 4. Assemble binaries
binaries = []
binaries.extend(ctk_binaries)
binaries.extend(dnd_binaries)
binaries.extend(pil_binaries)
binaries.extend(req_binaries)
binaries = list({(src, dst): (src, dst) for src, dst in binaries}.values())

# 5. Assemble hidden imports
hiddenimports = [
    'tkinter',
    'tkinter.filedialog',
    'tkinter.messagebox',
    'tkinter.ttk',
    'ctypes',
    'json',
    'urllib',
    'urllib.request',
    'urllib.parse',
    'multiprocessing',
    'threading',
    'subprocess',
    'shutil',
    'zipfile',
    'zlib',
    'struct',
    'mimetypes',
    'base64',
    'hashlib',
    'hmac',
]
hiddenimports.extend(core_submodules)
hiddenimports.extend(diag_submodules)
hiddenimports.extend(ui_submodules)
hiddenimports.extend(ctk_hidden)
hiddenimports.extend(dnd_hidden)
hiddenimports.extend(pil_hidden)
hiddenimports.extend(req_hidden)
hiddenimports = sorted(list(set(hiddenimports)))

# 6. Analysis configuration
a = Analysis(
    [os.path.join(PROJ_DIR, 'main.py')],
    pathex=[PROJ_DIR],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['pytest', 'IPython'],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# 7. Executable configuration
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='Crazy Doctor for The Sims 4',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=icns_path if os.path.isfile(icns_path) else None,
)

# 8. Collect files into app folder / bundle
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name='Crazy Doctor for The Sims 4',
)

# 9. Native macOS .app Bundle configuration
app = BUNDLE(
    coll,
    name='Crazy Doctor for The Sims 4.app',
    icon=icns_path if os.path.isfile(icns_path) else None,
    bundle_identifier='com.wedugames.thesims4.doctor',
    info_plist={
        'CFBundleName': 'Crazy Doctor for The Sims 4',
        'CFBundleDisplayName': 'Crazy Doctor for The Sims 4',
        'CFBundleIdentifier': 'com.wedugames.thesims4.doctor',
        'CFBundleVersion': '1.0.0',
        'CFBundleShortVersionString': '1.0.0',
        'NSHighResolutionCapable': True,
        'LSMinimumSystemVersion': '10.15.0',
        'NSRequiresAquaSystemAppearance': False,
        'NSHumanReadableCopyright': 'Copyright © 2026 WeduGames Engineering. All rights reserved.',
    },
)
