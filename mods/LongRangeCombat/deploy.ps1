# Run the packing script
" " | & "C:\dev\stalker2\unrealpak-main\UnrealPak-With-Compression.bat" "C:\dev\stalker2\mods\mods\LongRangeCombat\LongRangeCombat_P"

# Define source and destination
$SourceFile = "C:\dev\stalker2\mods\mods\LongRangeCombat\LongRangeCombat_P.pak"
$DestDir = "E:\SteamLibrary\steamapps\common\S.T.A.L.K.E.R. 2 Heart of Chornobyl\Stalker2\Content\Paks\~mods"

# Ensure the source file exists
if (-not (Test-Path $SourceFile)) {
    Write-Host "Error: Packed file not found at $SourceFile" -ForegroundColor Red
    exit 1
}

# Ensure destination directory exists
if (-not (Test-Path $DestDir)) {
    New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
    Write-Host "Created destination directory: $DestDir" -ForegroundColor Yellow
}

# Copy the file
Copy-Item -Path $SourceFile -Destination $DestDir -Force
Write-Host "Successfully deployed LongRangeCombat_P.pak to $DestDir" -ForegroundColor Green
