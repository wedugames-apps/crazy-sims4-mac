#!/usr/bin/env bash
# ==============================================================================
# Crazy Doctor for The Sims 4 (macOS Edition) - Native Cloud & Local Build Script
# ==============================================================================
# Builds:
# 1. Native macOS Application Bundle: 'Crazy Doctor for The Sims 4.app'
# 2. Distributable DMG installer with Applications drag-and-drop symlink:
#    'Crazy-Doctor-The-Sims-4-macOS.dmg'
# Compatible with Apple Silicon (M1/M2/M3/M4) and Intel (x86_64) runners.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

echo "=================================================================="
echo "⚡ BUILDING CRAZY DOCTOR FOR THE SIMS 4 (MACOS EDITION)"
echo "=================================================================="
echo "Host OS   : $(uname -s) $(uname -r)"
echo "Host Arch : $(uname -m)"
echo "Python    : $(python3 --version 2>&1 || true)"
echo "Directory : $SCRIPT_DIR"

# 1. Install or update required build dependencies
echo -e "\n📦 [1/4] Installing Python dependencies..."
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt
python3 -m pip install pyinstaller

# 2. Compile standalone macOS .app bundle via PyInstaller spec
echo -e "\n🔨 [2/4] Compiling macOS .app Bundle via PyInstaller..."
rm -rf build dist
pyinstaller --clean -y crazy_sims4_doctor_mac.spec

APP_PATH="dist/Crazy Doctor for The Sims 4.app"
if [ ! -d "$APP_PATH" ]; then
    echo "❌ Error: Application bundle not found at $APP_PATH"
    exit 1
fi
echo "✓ macOS .app Bundle created successfully: $APP_PATH"

# 3. Create DMG staging folder
echo -e "\n💿 [3/4] Packaging DMG Installer..."
DMG_STAGE="dist/dmg_stage"
rm -rf "$DMG_STAGE"
mkdir -p "$DMG_STAGE"

cp -R "$APP_PATH" "$DMG_STAGE/"
# Create drag-and-drop shortcut to /Applications
ln -s /Applications "$DMG_STAGE/Applications"

DMG_OUTPUT="dist/Crazy-Doctor-The-Sims-4-macOS.dmg"
rm -f "$DMG_OUTPUT"

# Use native macOS hdiutil to build compressed read-only DMG
if command -v hdiutil >/dev/null 2>&1; then
    echo "Creating DMG using native macOS hdiutil..."
    hdiutil create \
        -volname "Crazy Doctor for The Sims 4" \
        -srcfolder "$DMG_STAGE" \
        -ov \
        -format UDZO \
        "$DMG_OUTPUT"
    echo "✓ DMG created: $DMG_OUTPUT ($(du -sh "$DMG_OUTPUT" | cut -f1))"
else
    echo "⚠️ Warning: hdiutil not found (running in non-macOS environment)."
    echo "Packaging tar.gz archive as fallback..."
    tar -czf "dist/Crazy-Doctor-The-Sims-4-macOS.tar.gz" -C dist "Crazy Doctor for The Sims 4.app"
fi

rm -rf "$DMG_STAGE"

echo -e "\n=================================================================="
echo "🎉 BUILD SUCCESSFUL!"
echo "Artifacts generated in dist/:"
ls -lh dist/ || true
echo "=================================================================="
