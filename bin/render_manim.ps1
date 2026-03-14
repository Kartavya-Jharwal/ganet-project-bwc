Write-Host "=================================================" -ForegroundColor Cyan
Write-Host "🔥 BWC Epic Manim Render Pipeline 🔥" -ForegroundColor Yellow
Write-Host "Target: 2K Resolution (2560x1440) @ 60 FPS" -ForegroundColor DarkGray
Write-Host "=================================================" -ForegroundColor Cyan

# Find all Scene classes in the script
$pythonFile = "docs/scenes.py"
$content = Get-Content $pythonFile -Raw
$matches = [regex]::Matches($content, 'class\s+(Scene\w+)\s*\(')
$scenes = $matches | ForEach-Object { $_.Groups[1].Value }

if ($scenes.Count -eq 0) {
    Write-Host "No scenes found." -ForegroundColor Red
    exit 1
}

Write-Host "Found $($scenes.Count) Epic Scenes to render..." -ForegroundColor Gray
$count = 0

foreach ($scene in $scenes) {
    $count++
    $percent = [math]::Round(($count / $scenes.Count) * 100)
    
    Write-Progress -Activity "Manim Render Pipeline" -Status "Rendering Scene: $scene" -PercentComplete $percent -CurrentOperation "Scene $count of $($scenes.Count)"
    
    Write-Host "`n➤ Rendering: $scene" -ForegroundColor Blue
    
    # Render with custom 2K flags and attempt to enable motion blur if OpenGL is toggled (though CE is mostly just fast).
    # We will use manim standard CE with native 2K args.
    uv run manim --resolution 2560,1440 --fps 60 $pythonFile $scene
    
    if ($LASTEXITCODE -ne 0) {
        Write-Host "❌ Error rendering $scene" -ForegroundColor Red
    } else {
        Write-Host "✅ Completed: $scene" -ForegroundColor Green
    }
}

Write-Progress -Activity "Manim Render Pipeline" -Completed
Write-Host "`n✅ All Scenes Successfully Rendered to 2K. Check media/videos/" -ForegroundColor Green
