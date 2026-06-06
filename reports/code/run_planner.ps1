# Quick test with bundled samples (no SEO-as-Code parent required)
Set-Location $PSScriptRoot\..\..
if (-not (Test-Path "config\project.local.yaml")) {
    Copy-Item "config\project.local.yaml.example" "config\project.local.yaml"
    Write-Host "Created config/project.local.yaml from example (samples mode)."
}
py .\scripts\planner\pseo_planner.py @args
