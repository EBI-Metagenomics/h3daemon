# h3daemon

## Install

### Debian Bookworm

```sh
sudo apt update
sudo apt install python3 python3-pip python3-venv podman --yes
python3 -m pip install --user --no-warn-script-location pipx
python3 -m pipx ensurepath
export PATH=$HOME/.local/bin:$PATH
systemctl --user enable --now podman.socket
```
