# Run from the project ROOT:
#   powershell -ExecutionPolicy Bypass -File .\reorganize.ps1
#
# Before running: stop the server (Ctrl+C), run `deactivate`, and close Android Studio.

$ErrorActionPreference = "Stop"
$Root = (Get-Location).Path
$Utf8NoBom = New-Object System.Text.UTF8Encoding($false)

if ($env:VIRTUAL_ENV) {
    Write-Host "A virtual environment is active. Run 'deactivate', stop the server, then re-run." -ForegroundColor Red
    exit 1
}
if (-not (Test-Path (Join-Path $Root "index.html"))) {
    Write-Host "index.html not found here. Run this from the project root." -ForegroundColor Red
    exit 1
}

function Ensure-Dir($path) {
    if (-not (Test-Path $path)) { New-Item -ItemType Directory -Path $path -Force | Out-Null }
}

function Move-IfExists($from, $toDir) {
    if (Test-Path $from) {
        Ensure-Dir $toDir
        Move-Item -Path $from -Destination $toDir -Force
        Write-Host "  moved    $from -> $toDir" -ForegroundColor Green
    }
}

function Patch-File($path, $pairs) {
    if (-not (Test-Path $path)) { return }
    $text = [System.IO.File]::ReadAllText($path)
    foreach ($pair in $pairs) { $text = $text.Replace($pair[0], $pair[1]) }
    [System.IO.File]::WriteAllText($path, $text, $Utf8NoBom)
    Write-Host "  patched  $path" -ForegroundColor Cyan
}

Write-Host "`nReorganizing $Root`n" -ForegroundColor Cyan

# ---- web/ : the browser game ------------------------------------------------
Move-IfExists "index.html"       "web"
Move-IfExists "diagnostic.html"  "web"
foreach ($f in "database.js","stripe-config.js","payment-widget.js","premium.js","battle.js") {
    Move-IfExists $f "web/js"
}
foreach ($f in "ai_easy.py","ai_medium.py","game-engine.py") {
    Move-IfExists $f "web/py"
}

# ---- server/ : Python matchmaking server -----------------------------------
Move-IfExists "requirements.txt" "server"
Move-IfExists "test_flow.py"     "server/tests"

# ---- mobile/ : Capacitor + Android -----------------------------------------
foreach ($f in "package.json","package-lock.json","capacitor.config.json","android","node_modules") {
    Move-IfExists $f "mobile"
}

# ---- docs/ and tools/ ------------------------------------------------------
Move-IfExists "DEPLOYMENT.md"    "docs"
Move-IfExists "CHANGELOG.md"     "docs"
Move-IfExists "setup-server.ps1" "tools"

# ---- generated / junk (safe to delete) -------------------------------------
foreach ($junk in "dist","download",".venv") {
    if (Test-Path $junk) {
        Remove-Item -Recurse -Force $junk
        Write-Host "  removed  $junk" -ForegroundColor Yellow
    }
}

# ---- fix paths inside files ------------------------------------------------
Patch-File "web/index.html" @(
    @('src="stripe-config.js"',  'src="js/stripe-config.js"'),
    @('src="database.js"',       'src="js/database.js"'),
    @('src="ai_easy.py"',        'src="py/ai_easy.py"'),
    @('src="ai_medium.py"',      'src="py/ai_medium.py"'),
    @('src="game-engine.py"',    'src="py/game-engine.py"')
)
Patch-File "web/diagnostic.html" @(
    @('src="stripe-config.js"',  'src="js/stripe-config.js"')
)
Patch-File "mobile/capacitor.config.json" @(
    @('"webDir": "dist"', '"webDir": "../web"')
)
Patch-File "mobile/package.json" @(
    @('"main": "database.js"', '"main": "../web/js/database.js"')
)

# ---- .gitignore ------------------------------------------------------------
$gitignore = Join-Path $Root ".gitignore"
$wanted = @("server/.venv/", "mobile/node_modules/", "mobile/android/app/src/main/assets/public/",
            "__pycache__/", "*.pyc")
$existing = @()
if (Test-Path $gitignore) { $existing = Get-Content $gitignore }
$missing = $wanted | Where-Object { $existing -notcontains $_ }
if ($missing) { Add-Content -Path $gitignore -Value $missing }

# ---- GitHub Pages workflow (publishes web/) --------------------------------
Ensure-Dir (Join-Path $Root ".github/workflows")
$workflow = @'
name: Deploy web to GitHub Pages
on:
  push:
    branches: [main]
  workflow_dispatch:
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  deploy:
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/upload-pages-artifact@v3
        with:
          path: web
      - id: deployment
        uses: actions/deploy-pages@v4
'@
[System.IO.File]::WriteAllText((Join-Path $Root ".github/workflows/pages.yml"), $workflow, $Utf8NoBom)
Write-Host "  created  .github/workflows/pages.yml" -ForegroundColor Green

# ---- README ----------------------------------------------------------------
if (-not (Test-Path "README.md")) {
    $readme = @'
# Castle Go

- web/     browser game (index.html, js/, py/)
- server/  Python matchmaking server (FastAPI)
- mobile/  Capacitor + Android project
- docs/    deployment notes, changelog
- tools/   helper scripts
'@
    [System.IO.File]::WriteAllText((Join-Path $Root "README.md"), $readme, $Utf8NoBom)
}

Write-Host "`nDone. Root now holds README.md plus folders.`n" -ForegroundColor Cyan
Write-Host "Next:"
Write-Host "  python -m venv server\.venv"
Write-Host "  .\server\.venv\Scripts\Activate.ps1"
Write-Host "  pip install -r server\requirements.txt"
Write-Host "  uvicorn server.main:app --host 0.0.0.0 --port 8000"
