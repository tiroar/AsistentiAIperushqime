# How to Build APK for Asistenti i Ushqimeve AI

## Prerequisites
1. Install Node.js (https://nodejs.org/)
2. Install Android Studio (https://developer.android.com/studio)
3. Install Java JDK 11 or higher

## Steps to Build APK

### 1. Install Capacitor
```bash
npm install -g @capacitor/cli
```

### 2. Install Dependencies
```bash
npm install
```

### 3. Add Android Platform
```bash
npx cap add android
```

### 4. Sync Project
```bash
npx cap sync
```

### 5. Open in Android Studio
```bash
npx cap open android
```

### 6. Build APK in Android Studio
1. In Android Studio, go to **Build** → **Build Bundle(s) / APK(s)** → **Build APK(s)**
2. Wait for build to complete
3. APK will be created in: `android/app/build/outputs/apk/debug/app-debug.apk`

### 7. Sign APK (for production)
1. Generate keystore: `keytool -genkey -v -keystore asistenti-release-key.keystore -alias asistenti -keyalg RSA -keysize 2048 -validity 10000`
2. In Android Studio: **Build** → **Generate Signed Bundle / APK**
3. Choose APK and your keystore
4. Build signed APK

## Alternative: Use GitHub Actions (Automated)

Create `.github/workflows/build-apk.yml`:

```yaml
name: Build APK
on:
  push:
    branches: [ main ]
  workflow_dispatch:

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-node@v3
      with:
        node-version: '18'
    - uses: actions/setup-java@v3
      with:
        java-version: '11'
        distribution: 'temurin'
    - name: Install Capacitor
      run: npm install -g @capacitor/cli
    - name: Install dependencies
      run: npm install
    - name: Add Android platform
      run: npx cap add android
    - name: Sync project
      run: npx cap sync
    - name: Setup Android SDK
      uses: android-actions/setup-android@v2
    - name: Build APK
      run: |
        cd android
        ./gradlew assembleDebug
    - name: Upload APK
      uses: actions/upload-artifact@v3
      with:
        name: app-debug.apk
        path: android/app/build/outputs/apk/debug/app-debug.apk
```

## Download APK
Once built, the APK can be downloaded and installed directly on Android devices without Google Play Store.
