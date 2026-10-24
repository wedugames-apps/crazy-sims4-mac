# ⚡ Crazy Doctor for The Sims 4 (macOS Edition)
### Native Commercial Diagnostic, Metal Optimizer & Auto-Fixer Suite

A high-performance, native macOS desktop utility for The Sims 4 players and modders. Engineered specifically for **Apple Silicon (M1, M2, M3, M4)** and **Intel (x86_64)** Mac systems.

---

## 🌟 Native macOS Highlights

### 1. ⚡ Apple Metal API Graphics & Shader Pipeline
- **Metal Cache Purger**: Automatically cleans stale compiled Metal shaders from `~/Library/Caches/com.ea.TheSims4/` and `localthumbcache.package` to resolve pink flickering textures, UI tearing, and transition lag.
- **MacBook & iMac Thermal Limiter**:
  - **60 FPS** (Retina Standard): Ideal for MacBook Air, 13" MacBook Pro, Mac mini, and iMac.
  - **120 FPS** (Liquid Retina XDR ProMotion): Silky smooth, jitter-free performance on 14" and 16" MacBook Pro M-series displays.
  - Prevents runaway 500+ FPS menu loops, loud fan noise, and GPU thermal throttling.

### 2. ☁️ iCloud Drive Eviction & Ghost File Hydrator
- Detects files evicted by macOS *"Optimize Mac Storage"* (placeholder files with `.icloud` extensions or APFS dataless blocks).
- Automatically triggers kernel hydration via stream buffering and `brctl download` to eliminate infinite loading spins and game hangs.

### 3. 🔐 Unified 1-Key macOS Registration & Auto-Unlock
- **Zero-Friction Auto-Unlock**: If you already activated **EA Server Dashboard for Mac**, Crazy Doctor detects the existing registration cache (`~/Library/Application Support/EAshare/license_cache.json` / `WeduGames`) and automatically unlocks all VIP features instantly on startup.
- **1-Key Compatibility**: Accepts `WG-TS4M-XXXX-XXXX` license keys, validates against Cloudflare R2 (`wgtools-repo/user_accounts/`), binds logic board hardware UUID (`ioreg` / `sysctl`), and stores an offline cryptographic HMAC-SHA256 signature for offline play.

### 4. 🩺 WeduGames Doctor & Crazy Core Engine
- Multimodal visual troubleshooting: Attach screenshots or press **Cmd+V** to paste crash traces or visual glitches directly.
- Autonomous diagnostic engine analyzes Error 102/109, red-and-white question mark Sims, and corrupted UI mods, outputting 1-Click Action cards.
- Offline heuristics knowledge engine guarantees diagnosis even without active internet connection.

### 5. 🛠️ Complete Diagnostic & Mod Suite
- **DBPF 2.x Package Parser**: High-speed binary index reader, compression/decompression, and STBL v5 builder.
- **3D GEOM Mesh Hunter**: Profiles high-poly lag bombs (>30,000 polygons) and orphan recolors.
- **Lanczos 4K➔2K Texture Downsampler**: Reduces unified memory footprint by up to 60%.
- **Atomic Rolling Save Rollback**: Instant 1-Click restoration for corrupted save slots from `.save.ver0`–`.ver4` backups.
- **Script Depth Flattener**: Resolves the Sims 4 engine bug where `.ts4script` files 2+ subfolders deep are ignored.
- **Townie Sanitizer**: Clears `AllowForRandom` flags to stop random townies from wearing wild custom content.

---

## 🚀 GitHub Actions Cloud Build (No Mac Required)

Because this repository includes an automated GitHub Actions CI/CD workflow (`.github/workflows/build_macos.yml`), **you do not need a physical Mac to build the macOS edition**:

1. Push your changes to GitHub or navigate to the **Actions** tab on your GitHub repository.
2. Select the workflow: **"Build Crazy Doctor for The Sims 4 (macOS Native)"**.
3. Click **Run workflow** (or simply push to `main` / `master` / `macos`).
4. GitHub's cloud macOS runners (`macos-14` Apple Silicon & `macos-13` Intel) will:
   - Set up Python 3.12
   - Install dependencies & run unit tests
   - Build `Crazy Doctor for The Sims 4.app` via PyInstaller Universal2
   - Create the drag-and-drop installer `.dmg` (`Crazy-Doctor-The-Sims-4-macOS.dmg`)
5. Once complete, download the `.dmg` directly from the **Artifacts** section of the workflow run!

---

## 💻 Local macOS Build

If building on a Mac:
```bash
cd "Crazy The Sims 4 Mac"
chmod +x build_macos.sh
./build_macos.sh
```
The installer will be generated at:
`dist/Crazy-Doctor-The-Sims-4-macOS.dmg`

---

## 🖥️ Command Line Usage (Headless CLI)

Run full health diagnostics without GUI:
```bash
python3 main.py --scan
```

Execute 1-Click Auto-Fix All:
```bash
python3 main.py --fix
```

Ask the WeduGames Doctor:
```bash
python3 main.py --ask "Game freeze on loading screen after updating CC"
```

Activate License Key:
```bash
python3 main.py --activate "WG-TS4M-XXXX-XXXX"
```

Check Auto-Unlock status:
```bash
python3 main.py --check-license
```
