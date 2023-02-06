# Welcome to h3daemon 👋

> Command-line for running HMMER server on arm64 and amd64 machines via containers.

### 🏠 [Homepage](https://github.com/EBI-Metagenomics/h3daemon)

## ⚡️ Requirements

- Python >= 3.9
- Pip
- [Podman](https://podman.io) >= 3.4
- [Homebrew](https://brew.sh) on MacOS (recommended)
- [Pipx](https://pypa.github.io/pipx/) for Python package management (recommended)

### MacOS

Install Python and Podman:

```sh
brew update && brew install python podman pipx
```

Ensure that your `PATH` environment variable is all set:

```sh
pipx ensurepath
```

💡 You might need to close your terminal and reopen it for the changes to take effect.

### Ubuntu (and Debian-based distros)

Install Python and Podman:

```sh
sudo apt update && sudo apt install python3 python3-pip python3-venv podman
python3 -m pip install --user pipx
```

Ensure that your `PATH` environment variable is all set:

```sh
python3 -m pipx ensurepath
```

💡 You might need to close your terminal and reopen it for the changes to take effect.

## 📦 Install

```sh
pipx install deciphon
```

## Usage

```
 Usage: h3daemon [OPTIONS] COMMAND [ARGS]...

╭─ Options ─────────────────────────────────────────────────────╮
│ --version                                                     │
│ --help             Show this message and exit.                │
╰───────────────────────────────────────────────────────────────╯
╭─ Commands ────────────────────────────────────────────────────╮
│ info        Show namespace information.                       │
│ ls          List namespaces.                                  │
│ press       Press hmmer3 ASCII file.                          │
│ start       Start daemon.                                     │
│ stop        Stop namespace.                                   │
│ sys         Show Podman information.                          │
╰───────────────────────────────────────────────────────────────╯
```

### Example

Download `minifam.hmm` database:

```sh
pipx run blx get \
  fe305d9c09e123f987f49b9056e34c374e085d8831f815cc73d8ea4cdec84960 \
  minifam.hmm
```

Press it:

```sh
h3daemon press minifam.hmm
```

Start the daemon to listen on a random (available) port:

```sh
h3daemon start minifam.hmm
```

And stop it:

```sh
h3daemon stop minifam.hmm
```

## 👤 Author

- [Danilo Horta](https://github.com/horta)

## Show your support

Give a ⭐️ if this project helped you!
