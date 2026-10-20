[CmdletBinding()]
param(
    [switch]$PushToAnna
)

$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$Command,
        [Parameter(Mandatory = $true)][string[]]$Arguments
    )
    & $Command @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE : $Command $($Arguments -join ' ')"
    }
}

$repoRoot = Split-Path -Parent $PSScriptRoot
if (-not (Test-Path (Join-Path $repoRoot ".git"))) {
    throw "Could not find the Git repository at $repoRoot"
}

Push-Location $repoRoot
try {
    $changes = @(& git status --porcelain)
    if ($LASTEXITCODE -ne 0) {
        throw "Could not inspect Git status."
    }
    if ($changes.Count -gt 0) {
        $changes | ForEach-Object { Write-Host $_ }
        throw "Local changes are present. Commit or stash them first; this script will not overwrite them."
    }

    Write-Host "`n[1/7] Updating local main from GitHub..."
    Invoke-Checked "git" @("fetch", "origin", "main")
    $branch = (& git branch --show-current).Trim()
    if ($LASTEXITCODE -ne 0) {
        throw "Could not determine the current Git branch."
    }
    if ($branch -ne "main") {
        Invoke-Checked "git" @("switch", "main")
    }
    Invoke-Checked "git" @("pull", "--ff-only", "origin", "main")

    if (-not (Get-Command "node" -ErrorAction SilentlyContinue)) {
        throw "Node.js 22 or newer is required. Install it, reopen PowerShell, and rerun this script."
    }
    $nodeVersionText = (& node -p "process.versions.node").Trim()
    $nodeMajor = [int]($nodeVersionText.Split(".")[0])
    if ($nodeMajor -lt 22) {
        throw "Node.js 22 or newer is required; found $nodeVersionText."
    }
    if (-not (Get-Command "npm" -ErrorAction SilentlyContinue)) {
        throw "npm was not found. Install/re-enable Node.js, reopen PowerShell, and rerun this script."
    }
    if (-not (Get-Command "anna-app" -ErrorAction SilentlyContinue)) {
        Write-Host "Installing the Anna App CLI..."
        Invoke-Checked "npm" @("install", "--global", "@anna-ai/cli")
    }
    if (-not (Get-Command "anna-app" -ErrorAction SilentlyContinue)) {
        throw "Anna CLI is not on PATH. Reopen PowerShell and rerun this script."
    }

    Push-Location (Join-Path $repoRoot "anna-app")
    try {
        Write-Host "`n[2/7] Installing app dependencies..."
        Invoke-Checked "npm" @("install", "--no-audit", "--no-fund")
        Write-Host "`n[3/7] Building the Anna frontend bundle..."
        Invoke-Checked "npm" @("run", "build")
        Write-Host "`n[4/7] Running frontend tests..."
        Invoke-Checked "npm" @("test")
        Write-Host "`n[5/7] Validating manifest and Host API permissions..."
        Invoke-Checked "anna-app" @("validate", "--strict")
        Write-Host "`n[6/7] Checking generated JavaScript syntax..."
        Invoke-Checked "node" @("--check", "bundle/app.js")

        if ($PushToAnna) {
            Write-Host "`nChecking Anna account login..."
            & anna-app whoami
            if ($LASTEXITCODE -ne 0) {
                throw "Anna CLI is not logged in. Run 'anna-app login --host https://anna.partners' and rerun with -PushToAnna."
            }
            Write-Host "`n[7/7] Pushing the validated bundle to Anna's working draft..."
            Invoke-Checked "anna-app" @("apps", "push")
            Write-Host "`nAnna working draft updated. This is not a public release."
            Write-Host "Open https://anna.partners/developer, install/test the draft, then cut version 0.1.1 and complete the platform review/publish steps."
        } else {
            Write-Host "`nAll local build and validation checks passed."
            Write-Host "After local checks pass, rerun: .\scripts\Update-AnnaApp.ps1 -PushToAnna"
        }
    } finally {
        Pop-Location
    }
} finally {
    Pop-Location
}
