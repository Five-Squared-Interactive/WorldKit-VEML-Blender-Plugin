# Package the VEML Exporter addon for Blender installation
# Run this script to create a properly structured ZIP file

$addonName = "veml_exporter"
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$tempDir = Join-Path $scriptDir "temp_package"
$addonDir = Join-Path $tempDir $addonName
$zipPath = Join-Path $scriptDir "$addonName.zip"

# Clean up any existing temp directory or zip
if (Test-Path $tempDir) {
    Remove-Item -Recurse -Force $tempDir
}
if (Test-Path $zipPath) {
    Remove-Item -Force $zipPath
}

# Create addon directory structure
New-Item -ItemType Directory -Path $addonDir -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $addonDir "operators") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $addonDir "panels") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $addonDir "properties") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $addonDir "exporters") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $addonDir "importers") -Force | Out-Null
New-Item -ItemType Directory -Path (Join-Path $addonDir "utils") -Force | Out-Null

# Copy files
Copy-Item (Join-Path $scriptDir "__init__.py") $addonDir
Copy-Item (Join-Path $scriptDir "operators\*.py") (Join-Path $addonDir "operators")
Copy-Item (Join-Path $scriptDir "panels\*.py") (Join-Path $addonDir "panels")
Copy-Item (Join-Path $scriptDir "properties\*.py") (Join-Path $addonDir "properties")
Copy-Item (Join-Path $scriptDir "exporters\*.py") (Join-Path $addonDir "exporters")
Copy-Item (Join-Path $scriptDir "importers\*.py") (Join-Path $addonDir "importers")
Copy-Item (Join-Path $scriptDir "utils\*.py") (Join-Path $addonDir "utils")

# Create ZIP
Compress-Archive -Path $addonDir -DestinationPath $zipPath -Force

# Clean up temp directory
Remove-Item -Recurse -Force $tempDir

Write-Host "Created $zipPath" -ForegroundColor Green
Write-Host ""
Write-Host "To install in Blender:" -ForegroundColor Cyan
Write-Host "  1. Edit -> Preferences -> Add-ons"
Write-Host "  2. Click 'Install...'"
Write-Host "  3. Select '$zipPath'"
Write-Host "  4. Enable 'Import-Export: VEML Exporter'"
