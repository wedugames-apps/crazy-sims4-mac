"""
==============================================================================
Crazy The Sims 4 Project - 3D Mesh Hunter & Lag Bomb Profiler
==============================================================================
Scans the user's Mods directory to:
- Detect high-poly CC "Lag Bombs" (> 30,000 polygons) that crush game framerates
- Detect Broken/Missing LODs (where distant camera zoom still renders ultra-poly models)
- Hunt Missing Parent Meshes (Recolor-only CC packages whose base mesh is missing from Mods)
"""

import os
from typing import Dict, List, Optional, Set, Tuple
from core.dbpf import DBPFPackage, TYPE_CASP, TYPE_GEOM, TYPE_MODEL
from core.casp_geom import CaspGeomParser, GeomMeshInfo


class MeshHunterReport:
    """Detailed mesh diagnostic report for a single .package file."""

    def __init__(self, package_path: str):
        self.package_path: str = package_path
        self.filename: str = os.path.basename(package_path)
        self.total_polygons: int = 0
        self.max_polygons: int = 0
        self.is_lag_bomb: bool = False
        self.broken_lods: bool = False
        self.is_orphan_recolor: bool = False
        self.missing_mesh_instances: List[int] = []
        self.meshes: List[GeomMeshInfo] = []


class MeshHunter:
    """Profiles CC meshes and hunts broken 3D dependencies."""

    def __init__(self, mods_folder: str):
        self.mods_folder: str = os.path.abspath(mods_folder)
        self.lag_bombs: List[MeshHunterReport] = []
        self.broken_lod_packages: List[MeshHunterReport] = []
        self.orphan_recolors: List[MeshHunterReport] = []
        self.all_reports: List[MeshHunterReport] = []

    def scan_mods(self, max_packages: int = 1500) -> Dict[str, any]:
        """
        Performs an exhaustive scan of .package files in Mods/
        to identify 3D lag bombs and missing parent meshes.
        """
        self.lag_bombs.clear()
        self.broken_lod_packages.clear()
        self.orphan_recolors.clear()
        self.all_reports.clear()

        if not os.path.isdir(self.mods_folder):
            return {
                "scanned_count": 0,
                "lag_bomb_count": 0,
                "broken_lod_count": 0,
                "orphan_recolor_count": 0
            }

        # First pass: Collect all packages and their defined GEOM instances
        all_pkg_paths = []
        all_defined_geom_instances: Set[int] = set()

        for root, _, files in os.walk(self.mods_folder):
            for f in files:
                if f.lower().endswith(".package") and not f.lower().endswith(".disabled"):
                    all_pkg_paths.append(os.path.join(root, f))
                    if len(all_pkg_paths) >= max_packages:
                        break
            if len(all_pkg_paths) >= max_packages:
                break

        # Pass 1.5: Quick index of GEOM instances across all packages
        pkg_objects: Dict[str, DBPFPackage] = {}
        for p in all_pkg_paths:
            try:
                pkg = DBPFPackage(p)
                pkg_objects[p] = pkg
                for r in pkg.resources:
                    if r.res_type in (TYPE_GEOM, TYPE_MODEL):
                        all_defined_geom_instances.add(r.instance_id)
            except Exception:
                pass

        # Second pass: Deep analysis of mesh polycounts & CASP references
        for p, pkg in pkg_objects.items():
            report = MeshHunterReport(p)
            analysis = CaspGeomParser.analyze_package_meshes(pkg)

            report.total_polygons = analysis["total_polygons"]
            report.max_polygons = analysis["max_polygons"]
            report.is_lag_bomb = analysis["is_lag_bomb"]
            report.broken_lods = analysis["broken_lods"]
            report.meshes = analysis["meshes"]

            # Check if this package has CASP but NO local GEOMs,
            # and its referenced GEOM instances are missing from all other scanned mods
            if analysis["casp_count"] > 0 and analysis["geom_count"] == 0:
                missing_refs = [
                    ref for ref in analysis["missing_mesh_instances"]
                    if ref not in all_defined_geom_instances
                ]
                if missing_refs:
                    report.is_orphan_recolor = True
                    report.missing_mesh_instances = missing_refs
                    self.orphan_recolors.append(report)

            if report.is_lag_bomb:
                self.lag_bombs.append(report)
            if report.broken_lods:
                self.broken_lod_packages.append(report)

            self.all_reports.append(report)

        return {
            "scanned_count": len(self.all_reports),
            "lag_bomb_count": len(self.lag_bombs),
            "broken_lod_count": len(self.broken_lod_packages),
            "orphan_recolor_count": len(self.orphan_recolors),
            "lag_bombs": self.lag_bombs,
            "broken_lods": self.broken_lod_packages,
            "orphan_recolors": self.orphan_recolors
        }
