# Use GSC + SF exports from sibling SEO-as-Code-Toolkit repo
Set-Location $PSScriptRoot\..\..
$gsc = Get-ChildItem ..\data\raw\gsc*.csv -ErrorAction SilentlyContinue |
    Sort-Object LastWriteTime -Descending | Select-Object -First 1
# SF export: sf_html.csv (preferred) or any sf*.csv in data/raw
$sf = Get-ChildItem ..\data\raw\sf_html.csv -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $sf) {
    $sf = Get-ChildItem ..\data\raw\sf*.csv -ErrorAction SilentlyContinue |
        Sort-Object LastWriteTime -Descending | Select-Object -First 1
}
if (-not $gsc) {
    Write-Error "No GSC CSV in ..\data\raw\ — run SEO-as-Code Etapa 1 first."
    exit 1
}
Write-Host "GSC:" $gsc.FullName
$args = @("--gsc", $gsc.FullName)
if ($sf) {
    Write-Host "SF:" $sf.FullName
    $args += @("--sf", $sf.FullName)
}
py .\scripts\planner\pseo_planner.py @args
