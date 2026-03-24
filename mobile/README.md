# phi_dps_mobile

A new Flutter project.

## Getting Started

This project is a starting point for a Flutter application.

A few resources to get you started if this is your first Flutter project:

- [Lab: Write your first Flutter app](https://docs.flutter.dev/get-started/codelab)
- [Cookbook: Useful Flutter samples](https://docs.flutter.dev/cookbook)

For help getting started with Flutter development, view the
[online documentation](https://docs.flutter.dev/), which offers tutorials,
samples, guidance on mobile development, and a full API reference.

## Tests

From the `mobile/` directory:

```bash
flutter analyze
flutter test
```

- `test/widget_test.dart` — login shell smoke test.
- `test/auth_token_test.dart` — `/auth/token` JSON parsing (no network).

## iOS simulator: codesign “resource fork / detritus not allowed”

On **macOS Sequoia** (and newer), the `Flutter` engine binary can get a protected
`com.apple.provenance` extended attribute. **codesign** then fails with:

`resource fork, Finder information, or similar detritus not allowed`

**Fix (try in order):**

1. **Full Disk Access for the app that runs Flutter**  
   **System Settings → Privacy & Security → Full Disk Access** → enable **Terminal** (if you use Terminal.app) and/or **Cursor** (if you run `flutter` from the IDE terminal).  
   Then quit and reopen the terminal/IDE and run:

   ```bash
   cd mobile
   flutter clean
   flutter pub get
   cd ios && pod install && cd ..
   flutter run -d "iPhone 16e" --dart-define=PHI_DPS_API_BASE=http://127.0.0.1:8000
   ```

2. **Run Flutter from Apple Terminal.app** (not the IDE terminal), after Terminal has Full Disk Access.

3. **One-off strip** (if a build left a bad `Flutter.framework` on disk):

   ```bash
   xattr -cr build/ios/Debug-iphonesimulator/Flutter.framework
   ```

   If attributes still won’t clear, try the same command with `sudo` in Terminal.app.

**Workaround:** use the **Android emulator** (`flutter run -d emulator-5554`) — it does not hit this macOS codesign path.

## Android: `mergeDebugResources` / “Unable to delete directory … mergeDebugResources”

Gradle sometimes fails to delete incremental resource merge folders because another process still has files open (another `flutter run`, Android Studio indexing, antivirus, or a stuck Gradle daemon).

**Fix:**

1. Stop other Flutter/Gradle builds; quit Android Studio if it has the project open.
2. From `mobile/android`: `./gradlew --stop`
3. Remove build outputs: `rm -rf build android/app/build android/.gradle`
4. `flutter clean` then `flutter pub get`, then `flutter run` again.

On the **Android emulator**, the host machine’s `127.0.0.1` is not your Mac; use **`http://10.0.2.2:8000`** for a local API:

```bash
flutter run --dart-define=PHI_DPS_API_BASE=http://10.0.2.2:8000
```

### API not reachable / login fails on device

- **Android:** The app enables cleartext HTTP and declares `INTERNET` in `AndroidManifest.xml` so a **local HTTP** backend (`10.0.2.2` or LAN IP) can be reached. Production builds should use **HTTPS** and tighten network security if needed.
- **iOS:** `Info.plist` includes `NSAppTransportSecurity` → `NSAllowsLocalNetworking` for local development. HTTP to a **LAN IP** on a physical device may still require an exception domain or HTTPS — prefer HTTPS for staging/production.
- **Jobs list empty after login:** The backend returns **only jobs assigned to the logged-in engineer** on `GET /jobs`. Unassigned jobs must be assigned (dispatcher/admin) before they appear in the app.

**CocoaPods + locale:** if `pod install` errors with Unicode/encoding, use:

```bash
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```
