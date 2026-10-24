"""
==============================================================================
Crazy Doctor for The Sims 4 (macOS Edition) - Diagnostics Suite
==============================================================================
Diagnostics and auto-fix engines:
- graphics: Apple Metal API & Metal shader cache purger, MacBook FPS limiter
- cloud_merge: iCloud Drive eviction & ghost file hydrator, split merger
- ea_killer: macOS process manager terminating zombie background processes
- health_suite: Master health scoring (0-100) and 1-Click Auto-Fix All
- mesh_hunter: 3D geometry high-poly lag-bomb & orphan hunter
- script_doctor: Script depth flattener & crash log decoder
- rollback: Atomic rolling save rollback (.save.ver0-.ver4)
- search_5050: Binary search troubleshooting automator
- townie_sanitizer: Townie CC sanitizer (AllowForRandom = 0)
"""

from diagnostics.health_suite import MasterHealthSuite, HealthIssue
from diagnostics.graphics import GraphicsDiagnostic
from diagnostics.cloud_merge import CloudFolderManager
from diagnostics.ea_killer import ProcessKiller
from diagnostics.mesh_hunter import MeshHunter
from diagnostics.script_doctor import ScriptModFlattener, CrashDecoder
from diagnostics.rollback import SaveRecoveryDiagnostic
from diagnostics.townie_sanitizer import TownieSanitizer
from diagnostics.search_5050 import Method5050Automator, Method5050Automator as FiftyFiftyTroubleshooter
