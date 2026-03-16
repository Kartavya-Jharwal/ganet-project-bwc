"""Render all 17 curated Manim scenes at 4K 60fps.

Outputs MP4 files to frontend/media/ for embedding in the microsite.

Usage:
    uv run python scripts/render_manim.py
    uv run python scripts/render_manim.py --quality 4k
    uv run python scripts/render_manim.py --quality 1080p --scene Scene01
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

SCENES_FILE = Path("docs/scenes_final.py")
OUTPUT_DIR = Path("frontend/media")

ALL_SCENES = [
    "Scene01_GeometricBrownianMotion",
    "Scene02_MarkowitzEfficientFrontier",
    "Scene03_CapitalMarketLine",
    "Scene04_AlphaBetaOrthogonality",
    "Scene05_ConditionalValueAtRisk",
    "Scene06_KellyCriterionParabola",
    "Scene07_CovarianceGeometry",
    "Scene08_YieldCurveDynamics",
    "Scene09_JumpDiffusionPoisson",
    "Scene10_QuadraticVariationBrownianMotion",
    "Scene11_StochasticLocalVolatilitySurface",
    "Scene12_BWCArchitecture",
    "Scene13_FeatureEngineering",
    "Scene14_BacktestEngine",
    "Scene15_StressTesting",
    "Scene16_RegimePhaseShift",
    "Scene17_DataPipelineFlow",
]

QUALITY_FLAGS = {
    "4k": ["-qk", "--fps", "60"],
    "1080p": ["-qh", "--fps", "60"],
    "720p": ["-qm", "--fps", "30"],
    "preview": ["-ql"],
}


def render_scene(scene_name: str, quality: str = "4k") -> bool:
    flags = QUALITY_FLAGS.get(quality, QUALITY_FLAGS["4k"])
    cmd = [
        sys.executable, "-m", "manim",
        *flags,
        "--media_dir", str(OUTPUT_DIR),
        str(SCENES_FILE),
        scene_name,
    ]
    print(f"  Rendering {scene_name} at {quality}...")
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"  FAILED: {scene_name}")
        print(result.stderr[-500:] if result.stderr else "No stderr")
        return False
    print(f"  Done: {scene_name}")
    return True


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Manim scenes for BWC frontend")
    parser.add_argument("--quality", choices=list(QUALITY_FLAGS), default="4k")
    parser.add_argument("--scene", type=str, default=None, help="Render a single scene")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    scenes = [args.scene] if args.scene else ALL_SCENES
    total = len(scenes)
    success = 0

    print(f"Rendering {total} scenes at {args.quality} quality...")
    for scene in scenes:
        if render_scene(scene, args.quality):
            success += 1

    print(f"\nComplete: {success}/{total} scenes rendered to {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
