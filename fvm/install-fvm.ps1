#requires -Version 5.1

[CmdletBinding()]
param(
    # Use "latest" or a release tag such as "4.3.0".
    [string] $Version = "latest",

    # FVM is installed for the current user by default.
    [string] $InstallDir = (Join-Path $env:LOCALAPPDATA "fvm"),

    # Download again even when the requested version is already installed.
    [switch] $Force
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$repository = "leoafarias/fvm"
$executable = "fvm.exe"
$versionFile = ".installed-version"
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

    # Also make fvm available to the current PowerShell session.
    $processEntries = @($env:Path -split ';' | Where-Object { $_ })
    if (-not ($processEntries | Where-Object { $_.Trim().TrimEnd('\') -ieq $target })) {
        $env:Path = "$Directory;$env:Path"
    }
}

try {
    if ([Environment]::OSVersion.Platform -ne [PlatformID]::Win32NT) {
        throw "This installer only supports Windows."
    }
    if (-not [Environment]::Is64BitOperatingSystem) {
        throw "FVM standalone builds only support 64-bit Windows (x64 or arm64)."
    }

    # Prefer the operating-system architecture so this also works from 32-bit PowerShell.
    $architecture = $null
    try {
        $osArchitecture = [System.Runtime.InteropServices.RuntimeInformation]::OSArchitecture.ToString()
        if ($osArchitecture -eq "Arm64") {
            $architecture = "arm64"
        } elseif ($osArchitecture -eq "X64") {
            $architecture = "x64"
        }
    } catch {
        # RuntimeInformation may be unavailable on older .NET installations.
    }

    if (-not $architecture) {
        $architectureName = if ($env:PROCESSOR_ARCHITEW6432) {
            $env:PROCESSOR_ARCHITEW6432
        } else {
            $env:PROCESSOR_ARCHITECTURE
        }
        if ($architectureName -match "ARM64") {
            $architecture = "arm64"
        } elseif ($architectureName -match "AMD64") {
            $architecture = "x64"
        } else {
            throw "Unsupported Windows architecture: $architectureName"
        }
    }

    # GitHub requires TLS 1.2 on Windows PowerShell 5.1.
    [Net.ServicePointManager]::SecurityProtocol = [Net.ServicePointManager]::SecurityProtocol -bor [Net.SecurityProtocolType]::Tls12
    $headers = @{
        Accept       = "application/vnd.github+json"
        "User-Agent" = "fvm-powershell-installer"
    }

    if (-not $Version -or $Version -eq "latest") {
        Write-Step "Looking up the latest FVM release..."
        $releaseUri = "https://api.github.com/repos/$repository/releases/latest"
    } else {
        $tag = [Uri]::EscapeDataString($Version)
        Write-Step "Looking up FVM release '$Version'..."
        $releaseUri = "https://api.github.com/repos/$repository/releases/tags/$tag"
    }

    $release = Invoke-RestMethod -Uri $releaseUri -Headers $headers -UseBasicParsing
    $releaseVersion = [string] $release.tag_name
    $assetPattern = "*-windows-$architecture.zip"
    $assets = @($release.assets | Where-Object { $_.name -like $assetPattern })

    if ($assets.Count -ne 1) {
        throw "Could not find a unique '$assetPattern' asset in release '$releaseVersion'."
    }

    $installedVersionPath = Join-Path $InstallDir $versionFile
    if (-not $Force -and (Test-Path -LiteralPath (Join-Path $InstallDir $executable)) -and
        (Test-Path -LiteralPath $installedVersionPath)) {
        $installedVersion = (Get-Content -LiteralPath $installedVersionPath -Raw).Trim()
        if ($installedVersion -eq $releaseVersion) {
            Add-ToUserPath $InstallDir
            Write-Host "FVM $releaseVersion is already installed at '$InstallDir'." -ForegroundColor Green
            exit 0
        }
    }

    $tempDir = Join-Path ([IO.Path]::GetTempPath()) ("fvm-install-" + [Guid]::NewGuid().ToString("N"))
    $archivePath = Join-Path $tempDir "fvm.zip"
    $extractDir = Join-Path $tempDir "extract"
    New-Item -ItemType Directory -Path $extractDir -Force | Out-Null

    Write-Step "Downloading FVM $releaseVersion for Windows $architecture..."
    Invoke-WebRequest -Uri $assets[0].browser_download_url -Headers $headers -OutFile $archivePath -UseBasicParsing

    Write-Step "Extracting archive..."
    Expand-Archive -LiteralPath $archivePath -DestinationPath $extractDir -Force
    $downloadedExecutable = Get-ChildItem -LiteralPath $extractDir -Filter $executable -File -Recurse | Select-Object -First 1
    if (-not $downloadedExecutable) {
        throw "The downloaded archive does not contain $executable."
    }

    $sourceDir = $downloadedExecutable.Directory.FullName
    New-Item -ItemType Directory -Path $InstallDir -Force | Out-Null
    Copy-Item -Path (Join-Path $sourceDir "*") -Destination $InstallDir -Recurse -Force
    Set-Content -LiteralPath $installedVersionPath -Value $releaseVersion -Encoding ASCII

    Add-ToUserPath $InstallDir

    Write-Host "FVM $releaseVersion was installed successfully." -ForegroundColor Green
    Write-Host "Location: $InstallDir"
    Write-Host "Run 'fvm --version' to verify the installation."
} catch {
    Write-Host "FVM installation failed: $($_.Exception.Message)" -ForegroundColor Red
    exit 1
} finally {
    if ($tempDir -and (Test-Path -LiteralPath $tempDir)) {
        Remove-Item -LiteralPath $tempDir -Recurse -Force -ErrorAction SilentlyContinue
    }
}
