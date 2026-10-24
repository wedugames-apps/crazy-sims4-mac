"""
==============================================================================
Crazy Doctor for The Sims 4 (macOS Edition) - Metal API & GPU Diagnostic Engine
==============================================================================
Manages:
- Apple Metal API graphics pipeline configuration (macOS Options.ini parser)
- Native Metal shader cache purging (~/Library/Caches/com.ea.TheSims4/ & localthumbcache)
- MacBook & iMac thermal protection & FPS limiter (60Hz Retina / 120Hz Liquid Retina ProMotion)
"""

import os
import re
import glob
import shutil
import sys
from typing import Dict, List, Optional, Tuple


class GraphicsDiagnostic:
    """Diagnoses and configures Apple Metal graphics, shader caches, and MacBook FPS limits."""

    USER_CACHE_TARGETS = [
        ("localthumbcache.package", "file", "Thumbnail & mod interaction cache"),
        ("avatarcache.package", "file", "Avatar animation cache"),
        ("spotlight_*.package", "pattern", "Spotlight gallery cache"),
        ("cache", "dir", "Temporary game cache files"),
        ("cachestr", "dir", "String localization cache"),
        ("lotcacheddata", "dir", "Lot preview cache"),
        ("onlinestorage", "dir", "Online gallery storage cache"),
    ]

    def __init__(self, ts4_user_folder: str, game_install_folder: Optional[str] = None):
        self.ts4_user_folder: str = os.path.abspath(ts4_user_folder)
        self.game_install_folder: Optional[str] = (
            os.path.abspath(game_install_folder) if game_install_folder else None
        )
        self.options_ini_path: str = os.path.join(self.ts4_user_folder, "Options.ini")

        # Native macOS Metal shader cache paths
        home = os.path.expanduser("~")
        self.macos_metal_cache_dirs: List[str] = [
            os.path.join(home, "Library", "Caches", "com.ea.TheSims4"),
            os.path.join(home, "Library", "Caches", "The Sims 4"),
        ]

    # ------------------------------------------------------------------------
    # 1. APPLE METAL API GRAPHICS CONFIGURATION
    # ------------------------------------------------------------------------
    def get_graphics_mode(self) -> Dict[str, any]:
        """
        Reads Metal API and renderer configuration from macOS Options.ini.
        The Sims 4 on macOS runs on Apple's native Metal rendering pipeline.
        """
        result = {
            "mode": "Apple Metal API (macOS Native)",
            "is_metal": True,
            "options_ini_found": os.path.isfile(self.options_ini_path),
            "raw_setting": None,
            "vsync_enabled": False,
        }

        if not os.path.isfile(self.options_ini_path):
            return result

        try:
            with open(self.options_ini_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Metal setting on macOS Options.ini
            m_metal = re.search(r"^\s*metal\s*=\s*(\d+)", content, re.MULTILINE | re.IGNORECASE)
            if m_metal:
                val = int(m_metal.group(1))
                result["raw_setting"] = val
                result["is_metal"] = (val == 1)
                result["mode"] = "Apple Metal API (Active)" if val == 1 else "Metal API (Disabled)"
            else:
                # Native macOS version defaults to Metal
                result["mode"] = "Apple Metal API (Native High Performance)"

            m_vsync = re.search(r"^\s*vsync\s*=\s*(\d+)", content, re.MULTILINE | re.IGNORECASE)
            if m_vsync and int(m_vsync.group(1)) == 1:
                result["vsync_enabled"] = True

        except Exception as e:
            result["error"] = str(e)

        return result

    def set_metal_mode(self, enable_metal: bool = True) -> Tuple[bool, str]:
        """Ensures Apple Metal API is enabled in macOS Options.ini."""
        target_val = 1 if enable_metal else 0
        try:
            if not os.path.isfile(self.options_ini_path):
                if not os.path.isdir(self.ts4_user_folder):
                    return False, "The Sims 4 user folder not found."
                with open(self.options_ini_path, "w", encoding="utf-8") as f:
                    f.write(f"[Graphics]\nmetal = {target_val}\nvsync = 1\n")
                return True, "Successfully created Options.ini with Apple Metal API enabled."

            with open(self.options_ini_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            pattern = re.compile(r"^\s*metal\s*=.*$", re.MULTILINE | re.IGNORECASE)
            if pattern.search(content):
                new_content = pattern.sub(f"metal = {target_val}", content)
            else:
                if "[Graphics]" in content:
                    new_content = content.replace("[Graphics]", f"[Graphics]\nmetal = {target_val}")
                else:
                    new_content = f"metal = {target_val}\n" + content

            with open(self.options_ini_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return True, "Successfully configured Apple Metal API in Options.ini."
        except Exception as e:
            return False, f"Failed to update Options.ini: {e}"

    # ------------------------------------------------------------------------
    # 2. METAL SHADER & THUMBNAIL CACHE PURGER
    # ------------------------------------------------------------------------
    def inspect_cache_items(self) -> List[Dict[str, any]]:
        """
        Scans for cache files in:
        1. Sims 4 user folder (localthumbcache, avatarcache, spotlight, etc.)
        2. Native macOS Metal shader cache in ~/Library/Caches/com.ea.TheSims4/
        """
        cache_list: List[Dict[str, any]] = []

        # 1. User folder caches
        for target, target_type, desc in self.USER_CACHE_TARGETS:
            if target_type == "file":
                p = os.path.join(self.ts4_user_folder, target)
                if os.path.isfile(p):
                    sz = os.path.getsize(p)
                    cache_list.append({
                        "name": target,
                        "path": p,
                        "type": "file",
                        "size": sz,
                        "description": desc
                    })
            elif target_type == "dir":
                p = os.path.join(self.ts4_user_folder, target)
                if os.path.isdir(p):
                    sz = sum(
                        os.path.getsize(os.path.join(root, f))
                        for root, _, files in os.walk(p)
                        for f in files
                    )
                    cache_list.append({
                        "name": target,
                        "path": p,
                        "type": "dir",
                        "size": sz,
                        "description": desc
                    })
            elif target_type == "pattern":
                for p in glob.glob(os.path.join(self.ts4_user_folder, target)):
                    if os.path.isfile(p):
                        sz = os.path.getsize(p)
                        cache_list.append({
                            "name": os.path.basename(p),
                            "path": p,
                            "type": "file",
                            "size": sz,
                            "description": desc
                        })

        # 2. Native macOS Metal Shader Caches in ~/Library/Caches/com.ea.TheSims4/
        for cache_dir in self.macos_metal_cache_dirs:
            if os.path.isdir(cache_dir):
                metal_sz = sum(
                    os.path.getsize(os.path.join(root, f))
                    for root, _, files in os.walk(cache_dir)
                    for f in files
                )
                if metal_sz > 0 or os.path.exists(cache_dir):
                    cache_list.append({
                        "name": os.path.basename(cache_dir) + " (Metal Shader Cache)",
                        "path": cache_dir,
                        "type": "dir",
                        "size": metal_sz,
                        "description": "macOS Metal compiled pipeline & shader cache"
                    })

        return cache_list

    def purge_cache(self) -> Tuple[int, int]:
        """
        Purges both user folder caches and macOS Metal shader caches.
        Returns: (purged_item_count, bytes_freed)
        """
        items = self.inspect_cache_items()
        purged_count = 0
        bytes_freed = 0

        for item in items:
            p = item["path"]
            sz = item["size"]
            try:
                if item["type"] == "file" and os.path.isfile(p):
                    os.remove(p)
                    purged_count += 1
                    bytes_freed += sz
                elif item["type"] == "dir" and os.path.isdir(p):
                    shutil.rmtree(p, ignore_errors=True)
                    purged_count += 1
                    bytes_freed += sz
            except Exception:
                pass

        return purged_count, bytes_freed

    # ------------------------------------------------------------------------
    # 3. MACBOOK & IMAC THERMAL LIMITER (60Hz Retina & 120Hz ProMotion)
    # ------------------------------------------------------------------------
    def inspect_fps_limit(self) -> Dict[str, any]:
        """
        Inspects macOS Options.ini for VSync and ConfigOverride/GraphicsRules.sgr
        for maxFPS limits (60Hz Retina or 120Hz Liquid Retina ProMotion).
        """
        res = {
            "vsync_enabled": False,
            "max_fps_rule": None,
            "is_fps_limited": False,
            "display_profile": "Uncapped (Overheating Risk)",
            "overheating_risk": True
        }

        if os.path.isfile(self.options_ini_path):
            try:
                with open(self.options_ini_path, "r", encoding="utf-8", errors="ignore") as f:
                    content = f.read()
                m_vsync = re.search(r"^\s*vsync\s*=\s*(\d+)", content, re.MULTILINE | re.IGNORECASE)
                if m_vsync and int(m_vsync.group(1)) == 1:
                    res["vsync_enabled"] = True
                    res["is_fps_limited"] = True
                    res["overheating_risk"] = False
                    res["display_profile"] = "VSync Active"
            except Exception:
                pass

        override_dir = os.path.join(self.ts4_user_folder, "ConfigOverride")
        rules_file = os.path.join(override_dir, "GraphicsRules.sgr")
        if os.path.isfile(rules_file):
            try:
                with open(rules_file, "r", encoding="utf-8", errors="ignore") as f:
                    rules_content = f.read()
                m_fps = re.search(r"setprop\s+maxFPS\s+(\d+)", rules_content, re.IGNORECASE)
                if m_fps:
                    fps_val = int(m_fps.group(1))
                    res["max_fps_rule"] = fps_val
                    res["is_fps_limited"] = True
                    res["overheating_risk"] = False
                    if fps_val == 60:
                        res["display_profile"] = "60 FPS (MacBook Retina Standard)"
                    elif fps_val == 120:
                        res["display_profile"] = "120 FPS (Liquid Retina XDR ProMotion)"
                    else:
                        res["display_profile"] = f"{fps_val} FPS Custom Limit"
            except Exception:
                pass

        return res

    def apply_fps_limiter(self, target_fps: int = 60, force_vsync: bool = True) -> Tuple[bool, str]:
        """
        Applies MacBook thermal protection:
        1. Enables VSync in Options.ini
        2. Configures 'setprop maxFPS <target_fps>' in ConfigOverride/GraphicsRules.sgr
        Profiles:
        - 60 FPS (Retina 60Hz - MacBook Air, MacBook Pro 13", iMac, Mac mini)
        - 120 FPS (ProMotion 120Hz - MacBook Pro 14"/16" M-series Liquid Retina XDR)
        """
        # 1. Update Options.ini VSync
        if force_vsync:
            try:
                if os.path.isfile(self.options_ini_path):
                    with open(self.options_ini_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                    pat = re.compile(r"^\s*vsync\s*=.*$", re.MULTILINE | re.IGNORECASE)
                    if pat.search(content):
                        new_content = pat.sub("vsync = 1", content)
                    else:
                        new_content = f"vsync = 1\n{content}"
                    with open(self.options_ini_path, "w", encoding="utf-8") as f:
                        f.write(new_content)
                elif os.path.isdir(self.ts4_user_folder):
                    with open(self.options_ini_path, "w", encoding="utf-8") as f:
                        f.write("[Graphics]\nvsync = 1\n")
            except Exception:
                pass

        # 2. Write ConfigOverride rule
        override_dir = os.path.join(self.ts4_user_folder, "ConfigOverride")
        os.makedirs(override_dir, exist_ok=True)
        rules_file = os.path.join(override_dir, "GraphicsRules.sgr")

        override_rule = (
            f"# WeduGames Sims 4 macOS Power Optimizer - MacBook Thermal Protection\n"
            f"setprop maxFPS {target_fps}\n"
        )

        try:
            if os.path.isfile(rules_file):
                with open(rules_file, "r", encoding="utf-8", errors="ignore") as f:
                    current_rules = f.read()
                if "setprop maxFPS" in current_rules:
                    current_rules = re.sub(r"setprop\s+maxFPS\s+\d+", f"setprop maxFPS {target_fps}", current_rules)
                else:
                    current_rules = override_rule + "\n" + current_rules
                with open(rules_file, "w", encoding="utf-8") as f:
                    f.write(current_rules)
            else:
                with open(rules_file, "w", encoding="utf-8") as f:
                    f.write(override_rule)

            profile_name = "120 FPS (ProMotion)" if target_fps == 120 else f"{target_fps} FPS"
            return True, f"FPS successfully capped at {profile_name}. MacBook thermal protection active."
        except Exception as e:
            return False, f"Failed to apply FPS limit: {e}"
