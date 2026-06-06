@echo off
cd /d "%~dp0..\.."
if not exist "config\project.local.yaml" (
    copy "config\project.local.yaml.example" "config\project.local.yaml"
    echo Created config/project.local.yaml from example.
)
py .\scripts\planner\pseo_planner.py %*
