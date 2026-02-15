# Non-Interactive Usage of emu-docker

This guide demonstrates how to run `emu-docker` non-interactively, which is useful for automation, CI/CD pipelines, and scripted workflows.

## Overview

The `create` command is the primary non-interactive method for building Docker images with the Android Emulator. Unlike `interactive` mode, which prompts for user selections, `create` requires all parameters to be specified on the command line.

## Basic Syntax

```sh
emu-docker create <emuzip> <imgzip> [flags]
```

### Positional Arguments

| Argument | Description |
|---|---|
| `emuzip` | Emulator zip file path, or one of: `stable`, `canary`, `all`, or a numeric build ID |
| `imgzip` | System image zip file path, or a regex matching the image to retrieve. Examples: `"Q google_apis_playstore x86_64"`, `"P.*x86_64"` |

## Common Examples

### Build from Latest Stable Emulator with Android Q

```sh
emu-docker create stable "Q google_apis_playstore x86_64"
```

This uses the latest stable emulator build with an Android Q (API 29) system image that includes Google Play Store.

### Build with a Specific Device Template

```sh
emu-docker create stable "Q x86_64" --device PixelTablet
```

Available device templates include:
- `Pixel2` (default) - Portrait orientation, 1080x1920 @ 440dpi
- `PixelTablet` - Landscape orientation, 2560x1600 @ 320dpi

### Build with GPU Support

```sh
emu-docker create stable "Q" --gpu
```

Enables hardware GPU acceleration (requires NVIDIA GPU and nvidia-docker).

### Build, Tag, and Start Immediately

```sh
emu-docker create canary "P.*x86_64" --tag my-test --start
```

This command:
1. Uses the canary channel emulator
2. Matches any Android P (API 28) x86_64 system image
3. Tags the image as `my-test`
4. Starts the container after building (forwards ports 5555 and 8554, injects your ADB key)

### Build and Push to a Custom Repository

```sh
emu-docker create --push --repo us.gcr.io/my-project/ stable "Q"
```

Builds the image and pushes it to your specified Docker repository.

### Build with Custom Emulator Parameters

```sh
emu-docker create stable "Q x86_64" --extra -http-proxy http://proxy.example.com
```

The `--extra` flag passes additional parameters to the emulator at launch time.

## Useful Flags

| Flag | Default | Description |
|---|---|---|
| `--dest` | `./bld` | Destination directory for generated Docker files |
| `--tag` | `""` | Docker tag (defaults to emulator build ID if not specified) |
| `--repo` | `us-docker.pkg.dev/android-emulator-268719/images` | Repository prefix for the image name |
| `--push` | `false` | Push the image to the repository after building |
| `--gpu` | `false` | Build an image with GPU drivers for hardware acceleration |
| `--metrics` | `false` | Enable sending usage metrics to Google |
| `--no-metrics` | `false` | Disable collection of usage metrics |
| `--start` | `false` | Start the container after creation |
| `--device` | `Pixel2` | Device template to use (e.g., `Pixel2`, `PixelTablet`) |
| `--extra` | `""` | Additional commands passed to the emulator (must be last parameter) |

## Listing Available Images and Emulators

Before building, you can list all available system images and emulator versions:

```sh
# List x86/x86_64 images only
emu-docker list

# Include ARM images (not recommended - very slow)
emu-docker list --arm
```

## Accepting Licenses Non-Interactively

Before creating containers, you must accept the Android SDK licenses:

```sh
emu-docker licenses --accept
```

This accepts all licenses without prompting, which is useful for automated workflows.

## Complete Non-Interactive Workflow Example

```sh
# Activate the virtual environment
source ./configure.sh

# Accept licenses non-interactively
emu-docker licenses --accept

# Build an image with the latest stable emulator and Android Q
emu-docker create stable "Q google_apis_playstore x86_64" \
  --device Pixel2 \
  --tag my-emulator \
  --start

# Connect via ADB
adb connect localhost:5555
adb wait-for-device

# Verify connection
adb devices
```

## CI/CD Integration Example

For continuous integration pipelines:

```sh
#!/bin/bash
set -e

# Setup
source ./configure.sh
emu-docker licenses --accept

# Build image
emu-docker create stable "Q google_apis_playstore x86_64" \
  --tag ci-build-${BUILD_ID} \
  --device Pixel2

# Start container in background
docker run -d \
  --name emulator-ci \
  -e ADBKEY="$(cat ~/.android/adbkey)" \
  --device /dev/kvm \
  --publish 5555:5555/tcp \
  my-emulator:ci-build-${BUILD_ID}

# Wait for boot
adb connect localhost:5555
adb wait-for-device
while [ "$(adb shell getprop sys.boot_completed | tr -d '\r')" != "1" ]; do
  sleep 1
done

# Run tests
adb install app.apk
adb shell am instrument -w com.example.app.test/androidx.test.runner.AndroidJUnitRunner

# Cleanup
docker stop emulator-ci
docker rm emulator-ci
```

## Related Documentation

- [How to Launch](how-to-launch.md) - Comprehensive guide covering all launch methods
- [Main README](../README.md) - Project overview and quick start
- [Troubleshooting](../TROUBLESHOOTING.md) - Common issues and solutions
