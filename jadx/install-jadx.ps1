#requires -Version 5.1

[CmdletBinding()]
param(
    # Use "latest" or a release tag/version such as "v1.5.3" or "1.5.3".
    [string] $Version = "latest",

    # JADX is installed for the current user by default.
    [string] $InstallDir = (Join-Path $env:LOCALAPPDATA "jadx"),

    # Download again even when the requested version is already installed.
    [switch] $Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repository = "skylot/jadx"
$versionFile = ".installed-version"
$cliRelativePath = "bin\jadx.bat"
$guiRelativePath = "bin\jadx-gui.bat"
$tempDir = $null

function Write-Step([string] $Message) {
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Add-ToUserPath([string] $Directory) {
    $userPath = [Environment]::GetEnvironmentVariable("Path", "User")
    if ($null -eq $userPath) {
        $userPath = ""
    }

    $target = $Directory.TrimEnd('\')
    $pathEntries = @($userPath -split ';' | Where-Object { $_ })
    $alreadyPresent = $false

    foreach ($entry in $pathEntries) {
        if ($entry.Trim().TrimEnd('\') -ieq $target) {
            $alreadyPresent = $true
            break
        }
    }

    if (-not $alreadyPresent) {
        $newUserPath = if ($userPath.Trim()) { "$($userPath.TrimEnd(';'));$Directory" } else { $Directory }
        [Environment]::SetEnvironmentVariable("Path", $newUserPath, "User")
        Write-Step "Added '$Directory' to the user PATH."
    }

    # Also make JADX available to the current PowerShell session.
    $processEntries = @($env:Path -split ';' | Where-Object { $_ })
    if (-not ($processEntries | Where-Object { $_.Trim().TrimEnd('\') -ieq $target })) {
        $env:Path = "$Directory;$env:Path"
    }
}

try {
    if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
        throw "This installer only supports Windows."
    }

    # GitHub requires TLS 1.2 on Windows PowerShell 5.1.
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    $headers = @{
        Accept       = "application/vnd.github+json"
        "User-Agent" = "jadx-powershell-installer"
    }

    if (-not $Version -or $Version -eq "latest") {
        Write-Step "Looking up the latest JADX release..."
        $releaseUri = "https://api.github.com/repos/$repository/releases/latest"
    } else {
        $requestedTag = if ($Version.StartsWith("v")) { $Version } else { "v$Version" }
        $tag = [Uri]::EscapeDataString($requestedTag)
        Write-Step "Looking up JADX release '$requestedTag'..."
        $releaseUri = "https://api.github.com/repos/$repository/releases/tags/$tag"
    }

    $release = Invoke-RestMethod -Uri $releaseUri -Headers $headers -UseBasicParsing
    $releaseVersion = [string] $release.tag_name
    $releaseNumber = $releaseVersion -replace '^v', ''

    # Select the full CLI + GUI distribution, not a jadx-gui-only Windows bundle.
    $assetName = "jadx-$releaseNumber.zip"
    $assets = @($release.assets | Where-Object { $_.name -eq $assetName })
    if ($assets.Count -ne 1) {
        throw "Could not find the full '$assetName' CLI and GUI distribution in release '$releaseVersion'."
    }

    $binDir = Join-Path $InstallDir "bin"
    $installedVersionPath = Join-Path $InstallDir $versionFile
    if (-not $Force -and
        (Test-Path -LiteralPath (Join-Path $InstallDir $cliRelativePath)) -and
        (Test-Path -LiteralPath (Join-Path $InstallDir $guiRelativePath)) -and
        (Test-Path -LiteralPath $installedVersionPath)) {
        $installedVersion = (Get-Content -LiteralPath $installedVersionPath -Raw).Trim()
        if ($installedVersion -eq $releaseVersion) {
            Add-ToUserPath $binDir
            Write-Host "JADX $releaseVersion is already installed at '$InstallDir'." -ForegroundColor Green
            exit 0
        }
    }

    $tempDir = Join-Path ([IO.Path]::GetTempPath()) ("jadx-install-" + [Guid]::NewGuid().ToString("N"))
    $archivePath = Join-Path $tempDir "jadx.zip"
    $extractDir = Join-Path $tempDir "extract"
    New-Item -ItemType Directory -Path $extractDir -Force | Out-Null

    Write-Step "Downloading the full JADX $releaseVersion CLI and GUI distribution..."
    Invoke-WebRequest -Uri $assets[0].browser_download_url -Headers $headers -OutFile $archivePath -UseBasicParsing

    $digestProperty = $assets[0].PSObject.Properties["digest"]
    if ($digestProperty -and $digestProperty.Value -match '^sha256:(.+)$') {
        Write-Step "Verifying archive checksum..."
        $expectedHash = $Matches[1]
        $actualHash = (Get-FileHash -LiteralPath $archivePath -Algorithm SHA256).Hash
        if ($actualHash -ine $expectedHash) {
            throw "Archive checksum verification failed."
        }
    }

    Write-Step "Extracting archive..."
    Expand-Archive -LiteralPath $archivePath -DestinationPath $extractDir -Force

    $downloadedCli = Get-ChildItem -LiteralPath $extractDir -Filter "jadx.bat" -File -Recurse | Select-Object -First 1
    if (-not $downloadedCli) {
        throw "The downloaded archive does not contain the JADX command-line launcher."
    }

    $sourceDir = $downloadedCli.Directory.Parent.FullName
    if (-not (Test-Path -LiteralPath (Join-Path $sourceDir $guiRelativePath))) {
        throw "The downloaded archive does not contain the JADX GUI launcher."
    }

    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    Get-ChildItem -LiteralPath $InstallDir -Force | Remove-Item -Recurse -Force
    Get-ChildItem -LiteralPath $sourceDir -Force | Copy-Item -Destination $InstallDir -Recurse -Force
    Set-Content -LiteralPath $installedVersionPath -Value $releaseVersion -Encoding ASCII

    Add-ToUserPath $binDir

    Write-Host "JADX $releaseVersion was installed successfully." -ForegroundColor Green
    Write-Host "Location: $InstallDir"
    Write-Host "CLI: jadx --version"
    Write-Host "GUI: jadx-gui"

    if (-not (Get-Command java -ErrorAction SilentlyContinue)) {
        Write-Warning "Java was not found in PATH. Install a 64-bit Java 11 or later runtime before running JADX."
    }
} catch {
    Write-Host "JADX installation failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    if ($tempDir -and (Test-Path -LiteralPath $tempDir)) {
        Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
