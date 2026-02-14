# How to Launch the Android Emulator in Docker

This guide covers every way to run the Android Emulator using this project — from
pulling a pre-built image to deploying in the cloud. Each section documents all
flags, defaults, and behaviors.

For common issues and fixes, see [TROUBLESHOOTING.md](../TROUBLESHOOTING.md).

---

## Table of Contents

- [Prerequisites](#prerequisites)
- [Quick Start: Pre-built Hosted Containers](#quick-start-pre-built-hosted-containers)
  - [Available Images](#available-images)
  - [Connecting via ADB](#connecting-via-adb)
  - [Background / CI Usage](#background--ci-usage)
  - [Performance: tmpfs Data Partition](#performance-tmpfs-data-partition)
- [Building Your Own Container](#building-your-own-container)
  - [Initial Setup](#initial-setup)
  - [emu-docker licenses](#emu-docker-licenses)
  - [emu-docker list](#emu-docker-list)
  - [emu-docker interactive](#emu-docker-interactive)
  - [emu-docker create](#emu-docker-create)
  - [emu-docker cloud-build](#emu-docker-cloud-build)
- [Device Templates](#device-templates)
- [Running Containers with Shell Scripts](#running-containers-with-shell-scripts)
  - [run.sh](#runsh)
  - [run-with-gpu.sh](#run-with-gpush)
  - [run-in-script-example.sh](#run-in-script-examplesh)
- [Web Interface (Browser Access)](#web-interface-browser-access)
  - [Architecture Overview](#architecture-overview)
  - [create_web_container.sh Flags](#create_web_containersh-flags)
  - [Docker Compose Launch Commands](#docker-compose-launch-commands)
  - [Systemd Service Installation](#systemd-service-installation)
- [Cloud Deployment (cloud-init)](#cloud-deployment-cloud-init)
  - [Configuration Variables](#configuration-variables)
  - [GCE Metadata Mapping](#gce-metadata-mapping)
  - [Launch Example](#launch-example)
- [Environment Variables Reference](#environment-variables-reference)
- [Port Reference](#port-reference)
- [TURN Server Configuration](#turn-server-configuration)
  - [When You Need TURN](#when-you-need-turn)
  - [Runtime TURN (Environment Variable)](#runtime-turn-environment-variable)
  - [Build-time TURN (--extra Flag)](#build-time-turn---extra-flag)
  - [Static vs Dynamic Configuration](#static-vs-dynamic-configuration)
- [Image Naming Conventions](#image-naming-conventions)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

| Requirement | Details |
|---|---|
| **OS** | Linux only. The containers will not run on macOS or Windows. |
| **Python** | Python 3 with `python3-venv` (needed for the `emu-docker` CLI tool). |
| **Docker** | [Docker](https://docs.docker.com/engine/install/) installed and runnable as a [non-root user](https://docs.docker.com/install/linux/linux-postinstall/). |
| **Docker Compose** | Required for the web interface. |
| **ADB** | [Android Debug Bridge](https://developer.android.com/studio/command-line/adb) on your `PATH`. Installing the Android SDK command-line tools is sufficient. |
| **KVM** | `/dev/kvm` must be available. Run on bare metal, or on a VM with nested virtualization enabled. |

**Cloud provider KVM access:**

- **AWS** — Use [bare metal instances](https://aws.amazon.com/about-aws/whats-new/2019/02/introducing-five-new-amazon-ec2-bare-metal-instances/).
- **Azure** — Enable [nested virtualization](https://docs.microsoft.com/en-us/azure/virtual-machines/windows/nested-virtualization).
- **GCE** — Enable [nested virtualization](https://cloud.google.com/compute/docs/instances/enable-nested-virtualization-vm-instances). Note: GCE's Container-Optimized OS does not expose `/dev/kvm` by default — see [cloud-init/README.MD](../cloud-init/README.MD) for instructions to build a custom image.

Nested virtualization will give reduced performance compared to bare metal.

---

## Quick Start: Pre-built Hosted Containers

The fastest way to get a running emulator. No build step needed.

```sh
docker run \
  -e ADBKEY="$(cat ~/.android/adbkey)" \
  --device /dev/kvm \
  --publish 8554:8554/tcp \
  --publish 5555:5555/tcp \
  us-docker.pkg.dev/android-emulator-268719/images/30-google-x64:30.1.2
```

### Available Images

All images are hosted at `us-docker.pkg.dev/android-emulator-268719/images/`. See [REGISTRY.MD](../REGISTRY.MD) for the full list.

Current images include:

- `28-playstore-x64:30.1.2`
- `28-playstore-x64-no-metrics:30.1.2`
- `29-google-x64:30.1.2`
- `29-google-x64-no-metrics:30.1.2`
- `30-google-x64:30.1.2`
- `30-google-x64-no-metrics:30.1.2`

Images with `-no-metrics` do not send usage data to Google. See [Image Naming Conventions](#image-naming-conventions) for format details.

### Connecting via ADB

```sh
adb connect localhost:5555
adb devices
```

The device will appear as `localhost:5555` once the emulator finishes booting.

### Background / CI Usage

Run the container in detached mode (`-d`) and wait for boot:

```sh
docker run -d \
  -e ADBKEY="$(cat ~/.android/adbkey)" \
  --device /dev/kvm \
  --publish 8554:8554/tcp \
  --publish 5555:5555/tcp \
  us-docker.pkg.dev/android-emulator-268719/images/30-google-x64:30.1.2

adb connect localhost:5555
adb wait-for-device

# Wait for full boot
while [ "$(adb shell getprop sys.boot_completed | tr -d '\r')" != "1" ]; do
  sleep 1
done
```

See [run-in-script-example.sh](../run-in-script-example.sh) for a complete example.

### Performance: tmpfs Data Partition

Mount a tmpfs at `/data` for significantly better performance, especially under
nested virtualization:

```sh
docker run \
  -e ADBKEY="$(cat ~/.android/adbkey)" \
  --device /dev/kvm \
  --mount type=tmpfs,destination=/data \
  --publish 8554:8554/tcp \
  --publish 5555:5555/tcp \
  us-docker.pkg.dev/android-emulator-268719/images/30-google-x64:30.1.2
```

The container's launch script detects a mounted `/data` partition and
automatically copies the AVD home directory there.

---

## Building Your Own Container

### Initial Setup

Activate the virtual environment and install the `emu-docker` CLI:

```sh
source ./configure.sh
```

This creates a Python virtual environment and makes the `emu-docker` command
available. All subsequent `emu-docker` commands assume this environment is active.

### emu-docker licenses

Review and accept the Android SDK licenses. You must accept licenses before
creating containers.

```sh
emu-docker licenses           # Display licenses interactively
emu-docker licenses --accept  # Accept all licenses non-interactively
```

| Flag | Default | Description |
|---|---|---|
| `--accept` | `false` | Accept all licenses after displaying them. |

### emu-docker list

List all publicly available emulator builds and system images.

```sh
emu-docker list         # Show x86/x86_64 images
emu-docker list --arm   # Also show ARM images
```

| Flag | Default | Description |
|---|---|---|
| `--arm` | `false` | Display ARM images. ARM images are not hardware-accelerated and are extremely slow. |

Output format:

```
SYSIMG <codename> <tag> <abi> <api> <url> [<variant>]
EMU <channel> <version> <os> <url>
```

The optional `[<variant>]` suffix (e.g. `[ext18]`, `[Baklava]`) appears when
multiple system images share the same API level but differ by extension or
preview version.

### emu-docker interactive

Interactively select a device template, system image, and emulator version from
menus, then build a Docker image.

```sh
emu-docker interactive --start
```

The prompts appear in this order:

1. **Device template** — Choose the hardware profile (e.g. Pixel 2, Pixel Tablet).
2. **System image** — Choose the Android version, tag, and ABI.
3. **Emulator version** — Choose the emulator build.

| Flag | Default | Description |
|---|---|---|
| `--dest` | `./bld` | Destination directory for generated Docker files. |
| `--gpu` | `false` | Build an image with GPU drivers for hardware acceleration. |
| `--start` | `false` | Start the container after creation. Forwards ports 5555 and 8554; injects your `~/.android/adbkey` (not stored). |
| `--arm` | `false` | Display ARM images in the selection menu. ARM images are not hardware-accelerated and are extremely slow. |
| `--repo` | `us-docker.pkg.dev/android-emulator-268719/images` | Repository prefix for the created image. |
| `--extra` | `""` | Additional commands to pass to the emulator at launch (e.g., `-turncfg "curl -s ..."`). |

### emu-docker create

Build a Docker image from an emulator zip and a system image zip. This is the
primary non-interactive build command.

```sh
emu-docker create <emuzip> <imgzip> [flags]
```

**Positional arguments:**

| Argument | Description |
|---|---|
| `emuzip` | Emulator zip file path, or one of: `stable`, `canary`, `all`, or a numeric build ID. Using a build ID downloads an untested pre-release build. |
| `imgzip` | System image zip file path, or a regex matching the image to retrieve. All matching images are selected. Examples: `"P google_apis_playstore x86_64"`, `"W google_apis x86_64 \[ext19\]"`. Use `emu-docker list` to see available images. |

**Flags:**

| Flag | Default | Description |
|---|---|---|
| `--dest` | `./bld` | Destination directory for generated Docker files. |
| `--tag` | `""` | Docker tag. Defaults to the emulator build ID if not specified. |
| `--repo` | `us-docker.pkg.dev/android-emulator-268719/images` | Repository prefix for the image name. |
| `--push` | `false` | Push the image to the repository specified by `--repo`. |
| `--gpu` | `false` | Build an image with GPU drivers for hardware acceleration. |
| `--metrics` | `false` | Enable sending usage metrics to Google on graceful container exit. |
| `--no-metrics` | `false` | Disable collection of usage metrics. |
| `--start` | `false` | Start the container after creation. Forwards ports 5555 and 8554; injects your `~/.android/adbkey` (not stored). |
| `--sys` | `false` | Process the system image layer only (skip building the emulator layer). |
| `--device` | `Pixel2` | Device template to use (e.g. `Pixel2`, `PixelTablet`). Templates are located in `emu/templates/avd/`. |
| `--extra` | `""` | Additional commands passed to the emulator. Must be the last parameter. Example: `--extra -http-proxy http://proxy.example.com`. |

**Examples:**

```sh
# Build from the latest stable emulator + an Android Q x86_64 image
emu-docker create stable "Q google_apis_playstore x86_64"

# Build with GPU support
emu-docker create stable "Q" --gpu

# Build and push to a custom repository
emu-docker -v create --push --repo us.gcr.io/my-project/ stable "Q"

# Build, tag, and start immediately
emu-docker create canary "P.*x86_64" --tag my-test --start
```

### emu-docker cloud-build

Create a Cloud Build distribution for publishing container images to a GCE
repository. This is primarily for Google internal use.

```sh
emu-docker cloud-build <emuzip> <img> [flags]
```

**Positional arguments:**

| Argument | Default | Description |
|---|---|---|
| `emuzip` | *(required)* | Emulator zip file path, or `stable`, `canary`, or a numeric build ID. |
| `img` | `"P google_apis_playstore x86_64\|Q google_apis_playstore x86_64"` | Regex matching the system images to include. |

**Flags:**

| Flag | Default | Description |
|---|---|---|
| `--repo` | `us-docker.pkg.dev/android-emulator-268719/images` | Repository prefix. |
| `--dest` | `./bld` | Destination for generated Docker files. |
| `--git` | `false` | Create a git commit and push to the destination. |
| `--sys` | `false` | Write system image steps only (otherwise writes emulator steps). |
| `--device` | `Pixel2` | Device template to use (e.g. `Pixel2`, `PixelTablet`). Templates are located in `emu/templates/avd/`. |

---

## Device Templates

Device templates define the hardware profile (screen size, density, orientation,
etc.) used by the emulated Android device. Templates are stored in
`emu/templates/avd/` and discovered automatically at runtime.

Each template consists of two files:

- `<DeviceName>.ini` — AVD metadata file.
- `<DeviceName>.avd/config.ini` — Full hardware configuration.

**Built-in templates:**

| Name | Display Name | Screen | Orientation |
|---|---|---|---|
| `Pixel2` | Pixel2 | 1080x1920 @ 440dpi | Portrait |
| `PixelTablet` | Pixel Tablet | 2560x1600 @ 320dpi | Landscape |

**Adding a new template:**

1. Create `emu/templates/avd/<DeviceName>.ini` (copy from an existing `.ini`).
2. Create `emu/templates/avd/<DeviceName>.avd/config.ini` with the desired
   hardware properties. Set `avd.ini.displayname` for the menu label.
3. The new template will automatically appear in `emu-docker interactive` and
   be available via `--device <DeviceName>` in `create` and `cloud-build` modes.

---

## Running Containers with Shell Scripts

Three convenience scripts are provided for launching containers directly.

### run.sh

Basic launcher with ADB, console, and gRPC access.

```sh
./run.sh <container-id> [additional-emulator-params]
```

**Ports exposed:**

| Host Port | Container Port | Purpose |
|---|---|---|
| 8554 | 8554/tcp | gRPC endpoint |
| 5554 | 5554/tcp | Emulator console (requires TOKEN) |
| 5555 | 5555/tcp | ADB |

**Environment variables passed to the container:**

| Variable | Value | Description |
|---|---|---|
| `TOKEN` | `$(cat ~/.emulator_console_auth_token)` | Emulator console auth token. |
| `ADBKEY` | `$(cat ~/.android/adbkey)` | Private ADB key. |
| `TURN` | From host environment | TURN server configuration command. |
| `EMULATOR_PARAMS` | Additional args from command line | Extra parameters appended to the emulator launch command. |

### run-with-gpu.sh

Launcher with NVIDIA GPU hardware acceleration. Requires
[nvidia-docker](https://github.com/NVIDIA/nvidia-docker) (Docker 19.03+ has
native support).

```sh
./run-with-gpu.sh <container-id> [additional-emulator-params]
```

You must first build the container with `--gpu`:

```sh
emu-docker create stable Q --gpu
```

**Ports exposed:**

| Host Port | Container Port | Purpose |
|---|---|---|
| 8554 | 8554/tcp | gRPC endpoint |
| 5555 | 5555/tcp | ADB |

**What it does beyond `run.sh`:**

- Passes `--gpus all` to make all GPUs available to the container.
- Runs `xhost +si:localuser:root` to allow container display access.
- Mounts `/tmp/.X11-unix` for X11 communication with the host.
- Passes `-e DISPLAY` to forward the host's display variable.
- Prepends `-gpu host` to `EMULATOR_PARAMS`, which overrides the default `swiftshader_indirect` renderer.

A minimal X server (e.g., [Xvfb](https://en.wikipedia.org/wiki/Xvfb)) is
required on the host even if no UI is displayed.

### run-in-script-example.sh

Demonstrates running a container in the background and waiting for boot
completion. Useful as a template for CI pipelines.

```sh
./run-in-script-example.sh
```

This script is hardcoded to use
`us-docker.pkg.dev/android-emulator-268719/images/r-google-x64:30.0.23` and
maps host port 15555 to container port 5555 (a high port avoids interfering with
ADB's emulator scanning).

**What it does:**

1. Launches the container in detached mode (`docker run -d`).
2. Runs `adb connect localhost:15555`.
3. Runs `adb wait-for-device`.
4. Polls `adb shell getprop sys.boot_completed` in a loop until it returns `1`.
5. Prints the `docker stop` command to tear down the container.

---

## Web Interface (Browser Access)

### Architecture Overview

The web interface composes four containers via Docker Compose:

- **[Envoy](https://www.envoyproxy.io/)** — Edge proxy that provides TLS (self-signed cert), HTTP-to-HTTPS redirect, gRPC-Web proxying for the emulator, and JWT token verification.
- **[Nginx](https://www.nginx.com/)** — Serves the compiled React application.
- **[Firebase](https://firebase.google.com/)** *(optional)* — Provides authentication and authorization. Issues JWT tokens that Envoy validates to gate access to the emulator gRPC endpoint. Must be configured via `js/firebase_config.json`.
- **Emulator** — The emulator container with gRPC and WebRTC video bridge.

**Display modes:**

1. **PNG screenshots** — Requests an image every second via gRPC. Always works but low performance.
2. **WebRTC** — Real-time video stream. Requires peer-to-peer connectivity (may need a [TURN server](#turn-server-configuration)).

**Additional requirements for the web interface:**

- Ports 80 and 443 must be available on the host.
- NodeJS and npm must be installed (for building the React app).
- An emulator container must be built first (via `emu-docker create` or `emu-docker interactive`).

### create_web_container.sh Flags

```sh
./create_web_container.sh [-h] [-a] [-s] [-i]
```

| Flag | Description |
|---|---|
| `-h` | Show help and exit. |
| `-a` | Expose ADB. Requires `~/.android/adbkey` to be available at container launch. Adds the `js/docker/development.yaml` overlay to the compose configuration. |
| `-s` | Start the containers immediately after creation (runs `docker-compose up`). |
| `-i` | Install as a systemd service with files in `/opt/emulator`. |

**What the script does:**

1. Runs `make -C js deps` to compile JavaScript protobuf definitions.
2. Generates ADB keys if `~/.android/adbkey` does not exist.
3. Copies the private ADB key into `js/docker/certs/`.
4. Creates a Python virtual environment and installs `docker-compose`.
5. Runs `docker-compose build` with the selected YAML files.
6. Cleans up the copied ADB key.

### Docker Compose Launch Commands

**Standard launch (no ADB):**

```sh
docker-compose -f js/docker/docker-compose-build.yaml up
```

**With ADB exposed:**

```sh
docker-compose -f js/docker/docker-compose-build.yaml -f js/docker/development.yaml up
```

Then open <http://localhost> in your browser. Accept the self-signed certificate
warning to proceed.

### Systemd Service Installation

Pass `-i` to `create_web_container.sh` to install the emulator as a systemd
service:

```sh
./create_web_container.sh -i
```

This will:

1. Copy Docker Compose YAML files to `/opt/emulator/`.
2. Copy `~/.android/adbkey` to `/opt/emulator/adbkey`.
3. Install `js/docker/emulator.service` to `/etc/systemd/system/`.
4. Create placeholder gRPC cert/key files in `/etc/ssl/`.
5. Enable and start the `emulator` systemd service.

Tested on Debian/Ubuntu.

---

## Cloud Deployment (cloud-init)

The [cloud-init](../cloud-init/cloud-init) script automates provisioning a cloud
instance that pulls and runs an emulator container on first boot. It uses
[cloud-init](https://cloudinit.readthedocs.io/en/latest/), a cross-platform
standard supported by AWS, Azure, and GCE.

The script creates:

- A `kvm` group and an `aemu` user (UID 2000) with KVM access.
- Udev rules for `/dev/kvm` permissions.
- A configuration file at `/run/metadata/aemu`.
- Helper scripts for launching and stopping containers.
- An `aemu.service` systemd unit.

### Configuration Variables

All variables are defined in `/run/metadata/aemu`:

| Variable | Default | Description |
|---|---|---|
| `INSTANCE_COUNT` | `1` | Number of emulator containers to start. Each instance uses ~4 vCPUs and ~12 GB (4 GB RAM + 8 GB tmpfs). |
| `GRPC_PORT` | `8554` | Port for the first gRPC instance. Additional instances increment from this value (8555, 8556, ...). |
| `ADB_PORT` | `5555` | Port for the first ADB instance. Additional instances increment from this value (5556, 5557, ...). |
| `TURN` | `""` | TURN server configuration command (see [TURN Server Configuration](#turn-server-configuration)). |
| `EMULATOR_PARAMS` | `""` | Additional parameters appended to the emulator launch command. |
| `AVD_CONFIG` | `""` | Additional AVD configuration lines appended to `config.ini`. |
| `IMAGE` | `us-docker.pkg.dev/android-emulator-268719/images/30-google-x64:latest` | Docker image to pull and run. |
| `ADBKEY` | *(sample key in template)* | Private ADB key embedded in the container. Replace with your own. |

### GCE Metadata Mapping

On GCE, instance metadata attributes override the defaults in `/run/metadata/aemu`:

| GCE Metadata Key | Maps to Variable |
|---|---|
| `emulator_grpc_port` | `GRPC_PORT` |
| `emulator_adb_port` | `ADB_PORT` |
| `emulator_image` | `IMAGE` |
| `emulator_adbkey` | `ADBKEY` |
| `emulator_turn` | `TURN` |
| `emulator_avd_config` | `AVD_CONFIG` |
| `emulator_instance_count` | `INSTANCE_COUNT` |
| `emulator_emulator_params` | `EMULATOR_PARAMS` |

### Launch Example

Create a GCE instance with nested virtualization and custom metadata:

```sh
gcloud compute instances create aemu-example \
  --zone us-west1-b \
  --min-cpu-platform "Intel Haswell" \
  --image cos-dev-nested \
  --machine-type n1-highcpu-32 \
  --tags=http-server,https-server \
  --metadata-from-file user-data=cloud-init \
  --metadata=emulator_adbkey="$(cat ~/.android/adbkey)",emulator_adb_port=80,emulator_grpc_port=443
```

Connect from your local machine:

```sh
IP=$(gcloud compute instances describe aemu-example \
  --format='get(networkInterfaces[0].accessConfigs[0].natIP)')
adb connect $IP:80
```

---

## Environment Variables Reference

These environment variables are consumed by the container's
[launch-emulator.sh](../emu/templates/launch-emulator.sh) script at runtime.

| Variable | Description | How to provide |
|---|---|---|
| `ADBKEY` | Private ADB key contents. Enables `adb connect` to the container. Written to `/root/.android/adbkey` and then unset. | `-e ADBKEY="$(cat ~/.android/adbkey)"` or Docker secret at `/run/secrets/adbkey`. |
| `ADBKEY_PUB` | Public ADB key. An alternative to providing the private key. Appended to `/root/.android/adbkey.pub`. | `-e ADBKEY_PUB="$(cat ~/.android/adbkey.pub)"` |
| `TOKEN` | Emulator console auth token. When set, the console is forwarded from internal port 5556 to external port 5554 via `socat`. | `-e TOKEN="$(cat ~/.emulator_console_auth_token)"` or Docker secret at `/run/secrets/token`. |
| `EMULATOR_PARAMS` | Space-separated additional parameters appended to the emulator launch command. | `-e EMULATOR_PARAMS="-gpu host -memory 4096"` |
| `TURN` | Command that produces a JSON RTCConfiguration on stdout. Passed to the emulator as `-turncfg`. | `-e TURN="curl -s https://turn.example.com/config"` |
| `AVD_CONFIG` | Additional lines appended to the AVD's `config.ini` (e.g., `hw.lcd.density=480`). | `-e AVD_CONFIG="hw.lcd.density=480"` |
| `ANDROID_AVD_HOME` | Overrides the AVD home directory inside the container. Set automatically by the launch script to `/android-home`. | Generally not user-set. |

**Docker secrets:** The launch script checks for Docker secrets at
`/run/secrets/adbkey`, `/run/secrets/token`, `/run/secrets/grpc_cer`, and
`/run/secrets/grpc_key` before falling back to environment variables. Secrets
take priority over environment variables.

**Key priority order for ADB authentication:**

1. Docker secret at `/run/secrets/adbkey`
2. `ADBKEY` environment variable
3. `ADBKEY_PUB` environment variable
4. Auto-generated internal key (you will not be able to connect from the host)

---

## Port Reference

| Port | Protocol | Purpose | Used By |
|---|---|---|---|
| 5554 | TCP | Emulator console (telnet). Only active when `TOKEN` is set. | `run.sh`, container internal `socat` |
| 5555 | TCP | ADB (forwarded from container-internal port 5557 via `socat`). | All launch methods |
| 8554 | TCP | gRPC endpoint (used by Android Studio, WebRTC, and JS clients). | All launch methods |
| 80 | TCP | HTTP (redirected to 443 by Envoy). | Web interface |
| 443 | TCP | HTTPS (Envoy TLS termination). | Web interface |
| 8080 | TCP | TURN REST API (if using the included Python turn server). | TURN server setup |

Container-internal ports (not directly exposed):

| Port | Purpose |
|---|---|
| 5556 | Emulator console (internal, forwarded to 5554 when TOKEN is set). |
| 5557 | ADB (internal, forwarded to 5555). |

---

## TURN Server Configuration

### When You Need TURN

A [TURN](https://en.wikipedia.org/wiki/Traversal_Using_Relays_around_NAT) server
is needed when the emulator is on a network that is not publicly accessible and
WebRTC peer-to-peer connections cannot be established. This typically occurs when
the server is behind a NAT or firewall.

If you only use ADB or gRPC (no WebRTC video), TURN is not required.

### Runtime TURN (Environment Variable)

Pass the `TURN` environment variable when launching a container. The value must
be a shell command that:

- Produces a valid [JSON RTCConfiguration](https://developer.mozilla.org/en-US/docs/Web/API/RTCConfiguration) on stdout.
- Contains at least an `iceServers` array.
- Completes within 1000 ms.
- Exits with code 0 on success.

```sh
docker run \
  -e ADBKEY="$(cat ~/.android/adbkey)" \
  -e TURN="curl -s -X POST https://turn.example.com/config?key=MY_KEY" \
  --device /dev/kvm \
  --publish 8554:8554/tcp \
  --publish 5555:5555/tcp \
  <container-id>
```

### Build-time TURN (--extra Flag)

Embed the TURN configuration directly into the container image so every launch
uses it by default:

```sh
emu-docker create canary "R" \
  --extra \
  '-turncfg '\''printf {"iceServers":[{"urls":"turn:my.turn.org","username":"webrtc","credential":"password"}]}'\'' '
```

Note the escaping: `'\''` produces a literal single quote, `\"` escapes double
quotes inside the JSON.

### Static vs Dynamic Configuration

| Approach | Command | Use Case |
|---|---|---|
| **Static** | `printf '{"iceServers":[...]}'` | Fixed TURN credentials. Simple setup. |
| **Dynamic** | `curl -s https://turn-api.example.com/config` | Temporary credentials from a REST API. More secure — credentials rotate. |

The container ships with `curl`, so both approaches work out of the box. See
[js/turn/README.MD](../js/turn/README.MD) for a complete walkthrough including a
sample coturn server and Python REST API for temporary credentials.

---

## Image Naming Conventions

Images follow the format:

```
{api}-{sort}-{abi}:{tag}
```

| Component | Values | Description |
|---|---|---|
| `api` | `28`, `29`, `30`, ... | Android API level. |
| `sort` | `aosp`, `google`, `playstore` | **aosp** — Basic AOSP image. **google** — Includes Google Play services. **playstore** — Includes Google Play Store app and services. |
| `abi` | `x86`, `x64`, `a32`, `a64` | CPU architecture. `x86`/`x64` are hardware-accelerated. `a32`/`a64` (ARM) are not accelerated and are extremely slow. |
| `tag` | `30.1.2`, `latest`, ... | Emulator version or `latest`. |

**Examples:**

- `29-playstore-x86:30.1.2` — API 29, Play Store, 32-bit x86, emulator 30.1.2.
- `30-google-x64:latest` — API 30, Google APIs, 64-bit x86, latest emulator.
- `28-playstore-x64-no-metrics:30.1.2` — Same as above but with metrics collection disabled.

The `-no-metrics` suffix indicates the image does not send usage data to Google.

---

## Troubleshooting

**1. `emu-docker` command not found**

Activate the virtual environment first:

```sh
source ./configure.sh
```

**2. `Permission denied` when creating containers**

Enable sudoless Docker: follow the [post-install steps](https://docs.docker.com/install/linux/linux-postinstall/).

**3. `Unable to find ADB below $ANDROID_SDK_ROOT or on the path!`**

Install ADB. The Android SDK command-line tools package is sufficient. Ensure `adb` is on your `PATH`.

**4. Arguments in wrong order for `emu-docker create`**

The order is `<emuzip> <imgzip>`, not the reverse. If you get an error like `emulator-29.2.8.zip is not a zip file with a system image`, you swapped the arguments.

**5. No WebRTC video in the browser (PNG works)**

- Confirm the gRPC endpoint works by clicking the PNG button.
- Check the JavaScript console for `handleJsepMessage: {"start":{}}` — if that is the only message, the video bridge is not connecting.
- You likely need a [TURN server](#turn-server-configuration).
- Check container logs: `docker logs <container-id> | grep -E "pulse:|video:|version:"`

For all other issues, see the full [TROUBLESHOOTING.md](../TROUBLESHOOTING.md).
