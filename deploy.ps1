param(
    [Parameter(Mandatory=$false, Position=0)]
    [string]$ModName
)

$RootDir = "C:\dev\stalker2\mods"
$ModsBaseDir = Join-Path $RootDir "mods"
$UnrealPakBat = "C:\dev\stalker2\unrealpak-main\UnrealPak-With-Compression.bat"
$DestDir = "E:\SteamLibrary\steamapps\common\S.T.A.L.K.E.R. 2 Heart of Chornobyl\Stalker2\Content\Paks\~mods"

function Deploy-Mod([string]$Name) {
    if ([string]::IsNullOrWhiteSpace($Name)) { return }
    
    $ModPath = Join-Path $ModsBaseDir $Name
    $PackDir = Join-Path $ModPath "${Name}_P"
    $SourceFile = Join-Path $ModPath "${Name}_P.pak"

    if (-not (Test-Path $ModPath)) {
        Write-Host "Error: Mod directory not found at $ModPath" -ForegroundColor Red
        return
    }

    if (-not (Test-Path $PackDir)) {
        # Fallback: Check if the directory name itself is the one to pack if _P doesn't exist
        # But per rules, we usually have a _P folder.
        Write-Host "Warning: Pack directory not found at $PackDir. Skipping $Name." -ForegroundColor Yellow
        return
    }

    Write-Host "--- Packing mod: $Name ---" -ForegroundColor Cyan
    " " | & $UnrealPakBat $PackDir

    if (-not (Test-Path $SourceFile)) {
        Write-Host "Error: Packed file not found at $SourceFile" -ForegroundColor Red
        return
    }

    if (-not (Test-Path $DestDir)) {
        New-Item -ItemType Directory -Path $DestDir -Force | Out-Null
    }

    Write-Host "Deploying to: $DestDir" -ForegroundColor Gray
    Copy-Item -Path $SourceFile -Destination $DestDir -Force
    Write-Host "Successfully deployed ${Name}_P.pak`n" -ForegroundColor Green
}

$AvailableMods = Get-ChildItem -Path $ModsBaseDir -Directory | Select-Object -ExpandProperty Name
$Options = @("DEPLOY ALL") + $AvailableMods

if ([string]::IsNullOrWhiteSpace($ModName)) {
    $SelectedIndex = 0
    $Finished = $false

    while (-not $Finished) {
        Clear-Host
        Write-Host "`n  === S.T.A.L.K.E.R. 2 MOD DEPLOYER ===" -ForegroundColor DarkCyan
        Write-Host "  Use ARROW KEYS to select, ENTER to confirm, or type the INDEX.`n" -ForegroundColor Gray

        for ($i = 0; $i -lt $Options.Count; $i++) {
            if ($i -eq $SelectedIndex) {
                Write-Host "  >> " -NoNewline -ForegroundColor Green
                Write-Host "[$i] $($Options[$i])" -ForegroundColor White -BackgroundColor DarkGreen
            } else {
                Write-Host "     " -NoNewline
                Write-Host "[$i] $($Options[$i])" -ForegroundColor Gray
            }
        }
        Write-Host "`n  [ESC] Exit" -ForegroundColor DarkGray

        if ($Host.UI.RawUI.KeyAvailable) {
            $Key = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
            
            switch ($Key.VirtualKeyCode) {
                38 { # Up Arrow
                    $SelectedIndex = ($SelectedIndex - 1 + $Options.Count) % $Options.Count
                }
                40 { # Down Arrow
                    $SelectedIndex = ($SelectedIndex + 1) % $Options.Count
                }
                13 { # Enter
                    $Finished = $true
                }
                27 { # Escape
                    Write-Host "`nExiting..."
                    exit 0
                }
                48..57 { # 0-9 keys
                    $num = [int][char]$Key.Character - 48
                    if ($num -lt $Options.Count) {
                        $SelectedIndex = $num
                        $Finished = $true
                    }
                }
            }
        }
        Start-Sleep -Milliseconds 50
    }
    $Selection = $Options[$SelectedIndex]
} else {
    $Selection = $ModName
}

# Clean run
Clear-Host
Write-Host "=== Deployment Started ===`n" -ForegroundColor Cyan

if ($Selection -eq "DEPLOY ALL") {
    Write-Host "Target: ALL MODS`n" -ForegroundColor Yellow
    foreach ($m in $AvailableMods) {
        Deploy-Mod $m
    }
} else {
    Write-Host "Target: $Selection`n" -ForegroundColor Cyan
    Deploy-Mod $Selection
}

Write-Host "--- Deployment Complete ---" -ForegroundColor Cyan
