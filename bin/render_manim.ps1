
Write-Host "Rendering Algorithmic Storytelling via Manim..."
uv run manim -pqm docs/scenes.py ScatterToNetwork
uv run manim -pqm docs/scenes.py KruskalSequence
uv run manim -pqm docs/scenes.py NodeResizer
Write-Host "Manim rendering complete. Artifacts stored in media/videos/"

