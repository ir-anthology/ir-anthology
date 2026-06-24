#!/usr/bin/env bash
set -euo pipefail

sudo apt-get update
sudo apt-get install -y --no-install-recommends wget gpg ca-certificates
wget -qO - https://packages.qlever.dev/pub.asc \
  | sudo gpg --dearmor -o /usr/share/keyrings/qlever.gpg
echo "deb [arch=amd64 signed-by=/usr/share/keyrings/qlever.gpg] https://packages.qlever.dev/ $(. /etc/os-release && echo "${UBUNTU_CODENAME:-$VERSION_CODENAME}") main" \
  | sudo tee /etc/apt/sources.list.d/qlever.list > /dev/null
sudo apt-get update
sudo apt-get install -y --no-install-recommends qlever
pip install "fastapi[standard]" "PyJWT" "cryptography"