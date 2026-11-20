import java.util.Properties

// Backend URL baked in from the repo-root .env (PUBLIC_BASE_URL = cloudflared tunnel)
val rootEnv = Properties().apply {
    val f = rootProject.file("../.env")
    if (f.exists()) f.readLines().filter { "=" in it && !it.trimStart().startsWith("#") }
        .forEach { val (k, v) = it.split("=", limit = 2); setProperty(k.trim(), v.substringBefore("#").trim()) }
}
val backendUrl: String = rootEnv.getProperty("PUBLIC_BASE_URL", "").ifEmpty { "http://127.0.0.1:8000" }

plugins {
    id("com.android.application")
    id("org.jetbrains.kotlin.android")
}

android {
    namespace = "com.saathi.app"
    compileSdk = 35

    defaultConfig {
        applicationId = "com.saathi.app"
        minSdk = 24
        targetSdk = 35
        versionCode = 1
        versionName = "0.1-barebones"
        buildConfigField("String", "BACKEND_URL", "\"$backendUrl\"")
    }
    buildFeatures { buildConfig = true }
    compileOptions {
        sourceCompatibility = JavaVersion.VERSION_17
        targetCompatibility = JavaVersion.VERSION_17
    }
    kotlin { jvmToolchain(17) }
}

dependencies {
    // Agora RTC, audio-only build (Maven Central io.agora.rtc:voice-sdk, latest stable 4.x as of Nov 2026)
    implementation("io.agora.rtc:voice-sdk:4.6.4")
}
