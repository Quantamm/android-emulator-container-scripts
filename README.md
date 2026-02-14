# Android Emulator Container Scripts

This is a set of minimal scripts to run the emulator in a container for various
systems such as Docker, for external consumption. The scripts are compatible
with both Python version 2 and 3.

\*Note that this is still an experimental feature and we recommend installing
this tool in a [python virtual environment](https://docs.python.org/3/tutorial/venv.html).
Please file issues if you notice that anything is not working as expected.

# Documentation

For a comprehensive guide covering all launch methods, flags, environment
variables, and port mappings, see **[docs/how-to-launch.md](docs/how-to-launch.md)**.

# Requirements

- **Linux** — the containers will not run on macOS or Windows
- **Python 3** with `python3-venv`
- **[Docker](https://docs.docker.com/engine/install/)** runnable as a [non-root user](https://docs.docker.com/install/linux/linux-postinstall/)
- **[Docker Compose](https://docs.docker.com/compose/install/)** (for the web interface)
- **ADB** on your `PATH` (the Android SDK command-line tools are sufficient)
- **KVM** — `/dev/kvm` must be available (bare metal or nested virtualization)

For cloud provider KVM setup (AWS, Azure, GCE), see the
[Prerequisites](docs/how-to-launch.md#prerequisites) section of the full docs.

# Quick Start: Hosted Containers

Pre-built images are available in a public repository ([details](REGISTRY.MD)).
No build step needed:

```sh
docker run \
  -e ADBKEY="$(cat ~/.android/adbkey)" \
  --device /dev/kvm \
  --publish 8554:8554/tcp \
  --publish 5555:5555/tcp \
  us-docker.pkg.dev/android-emulator-268719/images/30-google-x64:30.1.2
```

Connect via ADB:

```sh
adb connect localhost:5555
```

For background/CI usage, run with `-d` and wait for boot:

```sh
docker run -d \
  -e ADBKEY="$(cat ~/.android/adbkey)" \
  --device /dev/kvm \
  --publish 8554:8554/tcp \
  --publish 5555:5555/tcp \
  us-docker.pkg.dev/android-emulator-268719/images/30-google-x64:30.1.2
adb connect localhost:5555
adb wait-for-device
```

# Quick Start: Build Your Own

Install the `emu-docker` CLI in a virtual environment:

```sh
source ./configure.sh
emu-docker -h
```

Interactively select and launch an emulator image:

```sh
emu-docker interactive --start
```

The interactive mode will prompt you to select a device template (e.g. Pixel 2,
Pixel Tablet), then a system image and emulator version.

To use a specific device template in non-interactive mode, pass `--device`:

```sh
emu-docker create stable "Q x86_64" --device PixelTablet
```

Then connect via ADB:

```sh
adb connect localhost:5555
```

For the full CLI reference (`emu-docker create`, `list`, `cloud-build`, GPU
support, pushing to a repository, and more), see
[docs/how-to-launch.md](docs/how-to-launch.md#building-your-own-container).

# Web Interface

The repository includes a Docker Compose setup that makes the emulator
accessible through a browser using WebRTC. It bundles Envoy, Nginx, and
optionally Firebase for authentication.

See [docs/how-to-launch.md](docs/how-to-launch.md#web-interface-browser-access)
for architecture details, setup instructions, and launch commands.

# Cloud Deployment

There is a sample cloud-init script that provides details on how you can configure an instance
that will automatically launch and configure an emulator on creation. Details on how to do this
can be found [here](cloud-init/README.MD).

### Troubleshooting

We have a separate [document](TROUBLESHOOTING.md) related to dealing with
issues.

### Modifying the demo

Details on the design and how to modify the React application can be found
[here](js/README.md)
