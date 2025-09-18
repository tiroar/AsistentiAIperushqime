#!/usr/bin/env python3
"""
Simple script to create a basic APK wrapper for the Streamlit app
This creates a WebView-based Android app that loads your Streamlit URL
"""

import os
import zipfile
import json
from pathlib import Path

def create_apk_structure():
    """Create the basic APK structure"""
    
    # Create directories
    os.makedirs("android_app/assets", exist_ok=True)
    os.makedirs("android_app/res/drawable", exist_ok=True)
    os.makedirs("android_app/res/values", exist_ok=True)
    os.makedirs("android_app/res/layout", exist_ok=True)
    os.makedirs("android_app/src/com/asistenti/ushqime", exist_ok=True)
    
    # AndroidManifest.xml
    manifest = '''<?xml version="1.0" encoding="utf-8"?>
<manifest xmlns:android="http://schemas.android.com/apk/res/android"
    package="com.asistenti.ushqime"
    android:versionCode="1"
    android:versionName="1.0">
    
    <uses-permission android:name="android.permission.INTERNET" />
    <uses-permission android:name="android.permission.ACCESS_NETWORK_STATE" />
    
    <application
        android:allowBackup="true"
        android:icon="@drawable/icon"
        android:label="@string/app_name"
        android:theme="@android:style/Theme.NoTitleBar.Fullscreen">
        
        <activity
            android:name=".MainActivity"
            android:exported="true"
            android:screenOrientation="portrait">
            <intent-filter>
                <action android:name="android.intent.action.MAIN" />
                <category android:name="android.intent.category.LAUNCHER" />
            </intent-filter>
        </activity>
    </application>
</manifest>'''
    
    with open("android_app/AndroidManifest.xml", "w") as f:
        f.write(manifest)
    
    # strings.xml
    strings = '''<?xml version="1.0" encoding="utf-8"?>
<resources>
    <string name="app_name">Asistenti i Ushqimeve AI</string>
    <string name="app_url">https://asistentiaiperushqime.streamlit.app</string>
</resources>'''
    
    with open("android_app/res/values/strings.xml", "w") as f:
        f.write(strings)
    
    # MainActivity.java
    main_activity = '''package com.asistenti.ushqime;

import android.app.Activity;
import android.os.Bundle;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;

public class MainActivity extends Activity {
    private WebView webView;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        setContentView(R.layout.activity_main);
        
        webView = findViewById(R.id.webview);
        WebSettings webSettings = webView.getSettings();
        webSettings.setJavaScriptEnabled(true);
        webSettings.setDomStorageEnabled(true);
        webSettings.setLoadWithOverviewMode(true);
        webSettings.setUseWideViewPort(true);
        webSettings.setBuiltInZoomControls(true);
        webSettings.setDisplayZoomControls(false);
        
        webView.setWebViewClient(new WebViewClient());
        webView.loadUrl(getString(R.string.app_url));
    }
    
    @Override
    public void onBackPressed() {
        if (webView.canGoBack()) {
            webView.goBack();
        } else {
            super.onBackPressed();
        }
    }
}'''
    
    with open("android_app/src/com/asistenti/ushqime/MainActivity.java", "w") as f:
        f.write(main_activity)
    
    # activity_main.xml
    layout = '''<?xml version="1.0" encoding="utf-8"?>
<LinearLayout xmlns:android="http://schemas.android.com/apk/res/android"
    android:layout_width="match_parent"
    android:layout_height="match_parent"
    android:orientation="vertical">
    
    <WebView
        android:id="@+id/webview"
        android:layout_width="match_parent"
        android:layout_height="match_parent" />
        
</LinearLayout>'''
    
    with open("android_app/res/layout/activity_main.xml", "w") as f:
        f.write(layout)
    
    print("✅ Android app structure created!")
    print("📁 Files created in: android_app/")
    print("\n🔧 To build APK:")
    print("1. Install Android Studio")
    print("2. Open android_app folder in Android Studio")
    print("3. Build → Build Bundle(s) / APK(s) → Build APK(s)")
    print("4. APK will be in: android_app/app/build/outputs/apk/debug/")

if __name__ == "__main__":
    create_apk_structure()
