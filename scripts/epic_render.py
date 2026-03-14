import os
import re
import subprocess
import sys
import time


def parse_scenes(file_path):
    with open(file_path, encoding="utf-8") as f:
        content = f.read()
    return re.findall(r"class\s+(Vis_[a-zA-Z_0-9]+)\(", content)


def render_scenes():
    scenes_file = "docs/combined_scenes.py"
    scenes = parse_scenes(scenes_file)

    if not scenes:
        print("No scenes found in the file.")
        return

    print("==================================================")
    print("BWC EPIC CINEMATIC RENDER PIPELINE INITIATED")
    print(f"Target: {len(scenes)} Scenes")
    print("Resolution: 2560x1440 @ 60 FPS (2K)")
    print("==================================================\n")

    python_exe = r".venv\Scripts\python.exe" if os.name == "nt" else "python"

    try:
        for idx, scene in enumerate(scenes, 1):
            print(f"\n[{idx}/{len(scenes)}] Rendering Engine Activating -> {scene}")
            print("-" * 50)

            # The exact, reliable command verified earlier
            cmd = [
                python_exe,
                "-m",
                "manim",
                "--resolution",
                "2560,1440",
                "--fps",
                "60",
                scenes_file,
                scene,
            ]

            # Use subprocess run to ensure process finishes before moving on
            start_time = time.time()
            result = subprocess.run(cmd, shell=False)
            duration = time.time() - start_time

            if result.returncode != 0:
                print(f"❌ Error rendering {scene}. Render process halted.")
                sys.exit(result.returncode)
            else:
                print(f"✅ Successfully rendered {scene} in {duration:.1f} seconds.\n")

        print("\n==================================================")
        print("🎉 ALL SCENES RENDERED SUCCESSFULLY!")
        print("Outputs located in: media/videos/scenes/1440p60/")
        print("==================================================")

    except KeyboardInterrupt:
        print("\nPipeline aborted by user.")
        sys.exit(1)


if __name__ == "__main__":
    render_scenes()
