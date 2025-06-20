# Official Foundry installation for Windows
Write-Host "Installing Foundry using the official method..." -ForegroundColor Cyan

# First, let's try to download foundryup-windows
$foundryupUrl = "https://raw.githubusercontent.com/foundry-rs/foundry/master/foundryup/foundryup"
$foundryupPath = "$env:TEMP\foundryup"

Write-Host "Downloading foundryup..." -ForegroundColor Yellow

try {
    # Download the foundryup script
    Invoke-WebRequest -Uri $foundryupUrl -OutFile $foundryupPath -UseBasicParsing
    Write-Host "Downloaded foundryup successfully" -ForegroundColor Green
    
    # Make it executable and run it
    & bash $foundryupPath
}
catch {
    Write-Host "Failed to use foundryup, trying alternative method..." -ForegroundColor Yellow
    
    # Alternative: Download pre-built binaries from GitHub releases
    $baseUrl = "https://github.com/foundry-rs/foundry/releases/latest/download/"
    
    # Create foundry directory
    $foundryDir = "$PWD\foundry"
    if (!(Test-Path $foundryDir)) {
        New-Item -ItemType Directory -Path $foundryDir | Out-Null
    }
    
    # Try to get the latest release info
    try {
        $latestRelease = Invoke-RestMethod -Uri "https://api.github.com/repos/foundry-rs/foundry/releases/latest"
        $assets = $latestRelease.assets
        
        Write-Host "Found release: $($latestRelease.tag_name)" -ForegroundColor Cyan
        
        # Look for Windows binaries
        $windowsAssets = $assets | Where-Object { $_.name -like "*windows*" -or $_.name -like "*win*" }
        
        if ($windowsAssets) {
            foreach ($asset in $windowsAssets) {
                Write-Host "Found Windows asset: $($asset.name)" -ForegroundColor Yellow
                Write-Host "Download URL: $($asset.browser_download_url)" -ForegroundColor Gray
            }
        }
        else {
            Write-Host "No Windows binaries found in the latest release" -ForegroundColor Red
        }
    }
    catch {
        Write-Host "Failed to get release information: $_" -ForegroundColor Red
    }
}

Write-Host "`nPlease download Foundry manually from:" -ForegroundColor Yellow
Write-Host "https://github.com/foundry-rs/foundry/releases" -ForegroundColor Cyan
Write-Host "`nOr use WSL (Windows Subsystem for Linux) and run:" -ForegroundColor Yellow
Write-Host "curl -L https://foundry.paradigm.xyz | bash" -ForegroundColor Cyan
