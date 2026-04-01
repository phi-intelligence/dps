param(
  # Default is preview-only (no changes). Pass -Apply to perform moves.
  [switch]$Apply
)

$ErrorActionPreference = "Stop"
$WhatIf = -not $Apply

function Ensure-Dir([string]$Path) {
  if (-not (Test-Path $Path)) { New-Item -ItemType Directory -Path $Path | Out-Null }
}

function Move-File([string]$From, [string]$To) {
  if (-not (Test-Path $From)) { return }
  $toDir = Split-Path -Parent $To
  Ensure-Dir $toDir
  if ($WhatIf) {
    Write-Host "WHATIF: Move `"$From`" -> `"$To`""
  } else {
    Move-Item -LiteralPath $From -Destination $To -Force
  }
}

# Base paths
$public = Join-Path $PSScriptRoot "..\public"
$srcLower = Join-Path $public "imagesv2"
$srcUpper = Join-Path $public "imagesV2"

# Resolve ".." segments to avoid path length/substring issues
$srcLowerResolved = $srcLower
$srcUpperResolved = $srcUpper
try { if (Test-Path $srcLower) { $srcLowerResolved = (Resolve-Path -LiteralPath $srcLower).Path } } catch {}
try { if (Test-Path $srcUpper) { $srcUpperResolved = (Resolve-Path -LiteralPath $srcUpper).Path } } catch {}

# 1) Consolidate casing: imagesV2 -> imagesv2 (directory rename)
if (Test-Path $srcUpper) {
  if ($WhatIf) {
    Write-Host "WHATIF: Rename `"$srcUpperResolved`" -> `"$srcLowerResolved`""
  } else {
    if (-not (Test-Path $srcLower)) {
      Rename-Item -LiteralPath $srcUpper -NewName "imagesv2"
    } else {
      # If both exist, we move files from imagesV2 into imagesv2 then delete imagesV2 manually.
      Get-ChildItem -LiteralPath $srcUpper -File -Recurse | ForEach-Object {
        $full = (Resolve-Path -LiteralPath $_.FullName).Path
        $rel = $full.Substring($srcUpperResolved.Length).TrimStart("\")
        $dest = Join-Path $srcLowerResolved $rel
        Ensure-Dir (Split-Path -Parent $dest)
        if ($WhatIf) { Write-Host "WHATIF: Move `"$full`" -> `"$dest`"" } else { Move-Item -LiteralPath $full -Destination $dest -Force }
      }
    }
  }
}

# 2) Ensure target structure
@(
  "branding",
  "home",
  "sectors",
  "commercial_mechanical",
  "commercial_electrical",
  "commercial_gas",
  "domestic_mechanical",
  "domestic_electrical"
) | ForEach-Object { Ensure-Dir (Join-Path $srcLower $_) }

# 2b) If previous run left files in imagesv2 root (e.g. _install.jpg), move them into the intended folders.
# Commercial - Electrical (legacy filenames)
Move-File (Join-Path $srcLower "_electric.jpg") (Join-Path $srcLower "commercial_electrical\commercial_electric.jpg")
Move-File (Join-Path $srcLower "_wiring.jpg") (Join-Path $srcLower "commercial_electrical\commercial_wiring.jpg")
Move-File (Join-Path $srcLower "_thermostat.jpg") (Join-Path $srcLower "commercial_electrical\commercial_thermostat.jpg")
Move-File (Join-Path $srcLower "_testing.jpg") (Join-Path $srcLower "commercial_electrical\commercial_testing.jpg")
Move-File (Join-Path $srcLower "_diagnosis.jpg") (Join-Path $srcLower "commercial_electrical\commercial_diagnosis.jpg")

# Commercial - Gas (legacy filenames)
Move-File (Join-Path $srcLower "_boiler.jpg") (Join-Path $srcLower "commercial_gas\commercial_boiler.jpg")
Move-File (Join-Path $srcLower "_repair.jpg") (Join-Path $srcLower "commercial_gas\commercial_repair.jpg")
Move-File (Join-Path $srcLower "_install.jpg") (Join-Path $srcLower "commercial_gas\commercial_install.jpg")
Move-File (Join-Path $srcLower "_inspect.jpg") (Join-Path $srcLower "commercial_gas\commercial_inspect.jpg")
Move-File (Join-Path $srcLower "_flue.jpg") (Join-Path $srcLower "commercial_gas\commercial_flue.jpg")

# Domestic - Mechanical (legacy filenames)
Move-File (Join-Path $srcLower "eating.jpg") (Join-Path $srcLower "domestic_mechanical\domestic_heating.jpg")
Move-File (Join-Path $srcLower "lumbing.jpg") (Join-Path $srcLower "domestic_mechanical\domestic_plumbing.jpg")
Move-File (Join-Path $srcLower "ump.jpg") (Join-Path $srcLower "domestic_mechanical\domestic_pump.jpg")
Move-File (Join-Path $srcLower "eak.jpg") (Join-Path $srcLower "domestic_mechanical\domestic_leak.jpg")
Move-File (Join-Path $srcLower "ot_water.jpg") (Join-Path $srcLower "domestic_mechanical\domestic_hot_water.jpg")

# 3) Branding / UI
Move-File (Join-Path $srcLower "logo.png") (Join-Path $srcLower "branding\logo.png")
Move-File (Join-Path $srcLower "logo_full.png") (Join-Path $srcLower "branding\logo_full.png")
Move-File (Join-Path $srcLower "logo_full_light.png") (Join-Path $srcLower "branding\logo_full_light.png")
Move-File (Join-Path $srcLower "logo_full_nobg.png") (Join-Path $srcLower "branding\logo_full_nobg.png")
Move-File (Join-Path $srcLower "logo_full_light_nobg.png") (Join-Path $srcLower "branding\logo_full_light_nobg.png")
Move-File (Join-Path $srcLower "gas_safe_logo.jpeg") (Join-Path $srcLower "branding\gas_safe_logo.jpeg")

# 4) Home
Move-File (Join-Path $srcLower "home_engineer.jpeg") (Join-Path $srcLower "home\home_engineer.jpeg")
Move-File (Join-Path $srcLower "home_electrical.jpg") (Join-Path $srcLower "home\home_electrical.jpg")
Move-File (Join-Path $srcLower "home_gas.jpg") (Join-Path $srcLower "home\home_gas.jpg")
Move-File (Join-Path $srcLower "home-staff.png") (Join-Path $srcLower "home\home-staff.png")

# 5) Sectors (homepage grid)
Move-File (Join-Path $srcLower "warehouse_new.jpg") (Join-Path $srcLower "sectors\warehouse.jpg")
Move-File (Join-Path $srcLower "offices.jpg") (Join-Path $srcLower "sectors\offices.jpg")
Move-File (Join-Path $srcLower "hospital.webp") (Join-Path $srcLower "sectors\hospital.webp")
Move-File (Join-Path $srcLower "university.jpg") (Join-Path $srcLower "sectors\university.jpg")
Move-File (Join-Path $srcLower "fire_station.jpeg") (Join-Path $srcLower "sectors\fire_station.jpeg")

# 6) Core service hero image
Move-File (Join-Path $srcLower "mechanical_service.webp") (Join-Path $srcLower "home\mechanical_service.webp")

# 7) Commercial - Electrical
Move-File (Join-Path $srcLower "commercial_electric.jpg") (Join-Path $srcLower "commercial_electrical\commercial_electric.jpg")
Move-File (Join-Path $srcLower "commercial_wiring.jpg") (Join-Path $srcLower "commercial_electrical\commercial_wiring.jpg")
Move-File (Join-Path $srcLower "commercial_thermostat.jpg") (Join-Path $srcLower "commercial_electrical\commercial_thermostat.jpg")
Move-File (Join-Path $srcLower "commercial_testing.jpg") (Join-Path $srcLower "commercial_electrical\commercial_testing.jpg")
Move-File (Join-Path $srcLower "commercial_diagnosis.jpg") (Join-Path $srcLower "commercial_electrical\commercial_diagnosis.jpg")

# 8) Commercial - Gas
Move-File (Join-Path $srcLower "commerical_boiler.jpg") (Join-Path $srcLower "commercial_gas\commercial_boiler.jpg")
Move-File (Join-Path $srcLower "commercial_repair.jpg") (Join-Path $srcLower "commercial_gas\commercial_repair.jpg")
Move-File (Join-Path $srcLower "commercial_install.jpg") (Join-Path $srcLower "commercial_gas\commercial_install.jpg")
Move-File (Join-Path $srcLower "commercial_inspect.jpg") (Join-Path $srcLower "commercial_gas\commercial_inspect.jpg")
Move-File (Join-Path $srcLower "commercial_flue.jpg") (Join-Path $srcLower "commercial_gas\commercial_flue.jpg")

# 9) Domestic - Mechanical
Move-File (Join-Path $srcLower "domestic_heating.jpg") (Join-Path $srcLower "domestic_mechanical\domestic_heating.jpg")
Move-File (Join-Path $srcLower "domestic_plumbing.jpg") (Join-Path $srcLower "domestic_mechanical\domestic_plumbing.jpg")
Move-File (Join-Path $srcLower "domestic_pump.jpg") (Join-Path $srcLower "domestic_mechanical\domestic_pump.jpg")
Move-File (Join-Path $srcLower "domestic_leak.jpg") (Join-Path $srcLower "domestic_mechanical\domestic_leak.jpg")
Move-File (Join-Path $srcLower "domestic_hot_water.jpg") (Join-Path $srcLower "domestic_mechanical\domestic_hot_water.jpg")

# 10) Domestic - Electrical
Move-File (Join-Path $srcLower "eicr.jpeg") (Join-Path $srcLower "domestic_electrical\eicr.jpeg")

# 11) Commercial mechanical folder: normalise filenames with spaces (optional but recommended)
Move-File (Join-Path $srcLower "commercial_mechanical\system balance.jpg") (Join-Path $srcLower "commercial_mechanical\system_balance.jpg")
Move-File (Join-Path $srcLower "commercial_mechanical\power flushing.jpg") (Join-Path $srcLower "commercial_mechanical\power_flushing.jpg")

Write-Host ""
Write-Host "Done. Re-run with -Apply to perform moves."
