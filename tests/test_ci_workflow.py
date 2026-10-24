"""
==============================================================================
Test Suite: CI/CD Workflow, Build Infrastructure & Zero-AI Enforcement
==============================================================================
Verifies:
- Production-readiness and syntax of .github/workflows/build_macos.yml
- macOS cloud runner definitions (macos-14 Apple Silicon & macos-13 Intel)
- PyInstaller spec integrity (crazy_sims4_doctor_mac.spec)
- Shell build script integrity (build_macos.sh)
- Zero occurrences of prohibited AI terminology across the entire macOS codebase
"""

import os
import re
import unittest

PROJECT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
WORKSPACE_DIR = os.path.dirname(PROJECT_DIR)


class TestCIWorkflowAndIntegrity(unittest.TestCase):
    def test_github_workflow_file_exists(self):
        wf_path = os.path.join(WORKSPACE_DIR, ".github", "workflows", "build_macos.yml")
        self.assertTrue(os.path.isfile(wf_path), f"Workflow file missing at {wf_path}")

        with open(wf_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Check required runner platforms
        self.assertIn("macos-14", content, "Missing macOS 14 (Apple Silicon) runner")
        self.assertIn("macos-13", content, "Missing macOS 13 (Intel) runner")

        # Check essential build and packaging steps
        self.assertIn("setup-python", content)
        self.assertIn("upload-artifact", content)
        self.assertIn("build_macos.sh", content)
        self.assertIn(".dmg", content)
        self.assertIn("workflow_dispatch", content)

    def test_build_macos_shell_script(self):
        sh_path = os.path.join(PROJECT_DIR, "build_macos.sh")
        self.assertTrue(os.path.isfile(sh_path), f"Build script missing at {sh_path}")

        with open(sh_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertTrue(content.startswith("#!/usr/bin/env bash"))
        self.assertIn("crazy_sims4_doctor_mac.spec", content)
        self.assertIn("hdiutil", content)
        self.assertIn("Crazy-Doctor-The-Sims-4-macOS.dmg", content)

    def test_pyinstaller_mac_spec(self):
        spec_path = os.path.join(PROJECT_DIR, "crazy_sims4_doctor_mac.spec")
        self.assertTrue(os.path.isfile(spec_path), f"Spec file missing at {spec_path}")

        with open(spec_path, "r", encoding="utf-8") as f:
            content = f.read()

        self.assertIn("Crazy Doctor for The Sims 4.app", content)
        self.assertIn("BUNDLE(", content)
        self.assertIn("icon.icns", content)
        self.assertIn("NSHighResolutionCapable", content)

    def test_zero_prohibited_ai_terminology(self):
        """
        Enforces strict compliance with user constraint:
        Zero occurrences of 'AI' terminology (using 'Crazy Core' and 'WeduGames Doctor').
        """
        prohibited_patterns = [
            re.compile(r'\bAI\b'),            # Standalone word AI
            re.compile(r'\bAI_', re.I),       # AI_ prefix
            re.compile(r'_AI\b', re.I),       # _AI suffix
            re.compile(r'ai_config', re.I),   # legacy config file name
            re.compile(r'Gemini', re.I),      # Google Gemini brand
            re.compile(r'Artificial Intelligence', re.I),
        ]

        allowed_files = {"test_ci_workflow.py"}  # This test file itself defines the patterns
        violations = []

        for root, dirs, files in os.walk(PROJECT_DIR):
            # Exclude cache and git
            if "__pycache__" in root or ".git" in root:
                continue

            for f in files:
                if f in allowed_files:
                    continue
                if not (f.endswith(".py") or f.endswith(".json") or f.endswith(".sh") or f.endswith(".spec") or f.endswith(".md")):
                    continue

                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, PROJECT_DIR)

                with open(full_path, "r", encoding="utf-8", errors="ignore") as fh:
                    for line_idx, line in enumerate(fh, 1):
                        # Skip compatibility comments or license text
                        for pat in prohibited_patterns:
                            if pat.search(line):
                                violations.append(f"{rel_path}:{line_idx}: {line.strip()}")

        self.assertEqual(
            len(violations), 0,
            f"Found prohibited AI terminology in {len(violations)} locations:\n" + "\n".join(violations[:15])
        )


if __name__ == "__main__":
    unittest.main()
