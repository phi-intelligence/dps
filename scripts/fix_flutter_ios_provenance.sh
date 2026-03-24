#!/usr/bin/env bash
set -euo pipefail

# Sequoia+/macOS sometimes adds com.apple.provenance / Finder detritus to the
# Flutter engine iOS simulator framework. Xcode then fails codesigning with:
#   resource fork, Finder information, or similar detritus not allowed
#
# Root cause (verified in this repo): the iOS simulator engine binary inside
# Flutter's SDK cache has com.apple.provenance:
#   .../Flutter.xcframework/ios-arm64_x86_64-simulator/Flutter.framework/Flutter

ENGINE_XCFRAMEWORK_DIR="bin/cache/artifacts/engine/ios/Flutter.xcframework"
# The simulator binary we verified contains `com.apple.provenance`
ENGINE_BIN="bin/cache/artifacts/engine/ios/Flutter.xcframework/ios-arm64_x86_64-simulator/Flutter.framework/Flutter"
FLUTTER_ROOT="${FLUTTER_ROOT:-/opt/homebrew/share/flutter}"
TARGET_DIR="${FLUTTER_ROOT}/${ENGINE_XCFRAMEWORK_DIR}"
TARGET_BIN="${FLUTTER_ROOT}/${ENGINE_BIN}"

if [[ ! -f "$TARGET_BIN" ]]; then
  echo "ERROR: expected engine binary not found:"
  echo "  $TARGET_BIN"
  exit 1
fi

echo "Current provenance xattrs (before):"
xattr -lr "$TARGET_BIN" || true

echo "Removing provenance + Finder detritus from engine cache (requires sudo)..."
echo "Engine xcframework dir: $TARGET_DIR"

# 1) Aggressive recursive clear
sudo xattr -cr "$TARGET_DIR"

# 2) Explicit deletes (in case anything survives recursive clear)
sudo xattr -r -d com.apple.provenance "$TARGET_DIR" || true
sudo xattr -r -d com.apple.FinderInfo "$TARGET_DIR" || true
sudo xattr -r -d 'com.apple.fileprovider.fpfs#P' "$TARGET_DIR" || true

echo "Current provenance xattrs (after):"
xattr -lr "$TARGET_BIN" || true

if xattr -lr "$TARGET_BIN" 2>/dev/null | awk '/com\\.apple\\.provenance:/ {found=1} END {exit(found?0:1)}'; then
  echo "ERROR: com.apple.provenance is still present on engine simulator binary."
  echo "The script couldn't remove it; try rerunning after ensuring Full Disk Access "
  echo "is granted to Terminal.app (then quit/reopen Terminal)."
  exit 2
fi

echo "OK: com.apple.provenance no longer reported on the engine simulator binary."

echo "Done."

