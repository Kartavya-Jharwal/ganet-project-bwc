import re
import subprocess
import sys
import time
from pathlib import Path


SCENE_GROUPS = [
    (Path("docs/combined_scenes.py"), r"class\s+(Vis_[a-zA-Z_0-9]+)\("),
    (Path("docs/project_scenes.py"), r"class\s+(Scene\d+_[a-zA-Z_0-9]+)\("),
]
MEDIA_DIR = Path("media")
MASTER_OUTPUT = MEDIA_DIR / "videos" / "master_4k" / "bwc_master_4k.mp4"


def parse_scenes(file_path: Path, pattern: str) -> list[str]:
    content = file_path.read_text(encoding="utf-8")
    return re.findall(pattern, content)


def resolve_scene_output(scene_file: Path, scene_name: str) -> Path:
    return (
        MEDIA_DIR
        / "videos"
        / scene_file.stem
        / "2160p60"
        / f"{scene_name}.mp4"
    )


def render_scene(scene_file: Path, scene_name: str) -> int:
    python_exe = r".venv\Scripts\python.exe" if sys.platform == "win32" else "python"
    cmd = [
        python_exe,
        "-m",
        "manim",
        "--media_dir",
        str(MEDIA_DIR),
        "--resolution",
        "3840,2160",
        "--fps",
        "60",
        str(scene_file),
        scene_name,
    ]
    return subprocess.run(cmd, shell=False).returncode


def stitch_master(clips: list[Path], output_file: Path) -> int:
    output_file.parent.mkdir(parents=True, exist_ok=True)
    concat_file = output_file.parent / "concat_list.txt"
    concat_payload = "\n".join([f"file '{clip.resolve().as_posix()}'" for clip in clips])
    concat_file.write_text(concat_payload + "\n", encoding="utf-8")

    ffmpeg_cmd = [
        "ffmpeg",
        "-y",
        "-f",
        "concat",
        "-safe",
        "0",
        "-i",
        str(concat_file),
        "-c",
        "copy",
        str(output_file),
    ]
    return subprocess.run(ffmpeg_cmd, shell=False).returncode


def render_scenes() -> None:
    all_scene_targets: list[tuple[Path, str]] = []
    for scene_file, pattern in SCENE_GROUPS:
        scenes = parse_scenes(scene_file, pattern)
        all_scene_targets.extend((scene_file, scene_name) for scene_name in scenes)

    if not all_scene_targets:
        print("No scenes found in the configured files.")
        return

    print("==================================================")
    print("BWC MASTERPIECE RENDER PIPELINE INITIATED")
    print(f"Target: {len(all_scene_targets)} Scenes")
    print("Sequence: combined_scenes.py -> project_scenes.py")
    print("Resolution: 3840x2160 @ 60 FPS (4K Cinema)")
    print("==================================================\n")

    rendered_clips: list[Path] = []
    try:
        total = len(all_scene_targets)
        for idx, (scene_file, scene_name) in enumerate(all_scene_targets, 1):
            print(f"\n[{idx}/{total}] Rendering -> {scene_file.name}:{scene_name}")
            print("-" * 60)
            start_time = time.time()
            result_code = render_scene(scene_file, scene_name)
            duration = time.time() - start_time

            if result_code != 0:
                print(f"FAILED: {scene_name}. Pipeline halted.")
                sys.exit(result_code)

            output_clip = resolve_scene_output(scene_file, scene_name)
            if not output_clip.exists():
                print(f"FAILED: Expected clip missing at {output_clip}")
                sys.exit(2)

            rendered_clips.append(output_clip)
            print(f"DONE: {scene_name} in {duration:.1f}s")

        stitch_code = stitch_master(rendered_clips, MASTER_OUTPUT)
        if stitch_code != 0:
            print("FAILED: Stitch step did not complete. Ensure ffmpeg is installed and available.")
            sys.exit(stitch_code)

        print("\n==================================================")
        print("ALL 4K SCENES RENDERED AND STITCHED SUCCESSFULLY")
        print(f"Master Output: {MASTER_OUTPUT}")
        print("==================================================")

    except KeyboardInterrupt:
        print("\nPipeline aborted by user.")
        sys.exit(1)


if __name__ == "__main__":
    render_scenes()