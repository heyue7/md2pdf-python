#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${1:-$(pwd)}"
WHEEL_PATH=""

shopt -s nullglob
wheels=("$PWD"/md2pdf_cli-*.whl "$PWD"/dist/md2pdf_cli-*.whl)
if [[ ${#wheels[@]} -gt 0 ]]; then
  IFS=$'\n' sorted=($(ls -1t "${wheels[@]}"))
  WHEEL_PATH="${sorted[0]}"
fi
shopt -u nullglob

if [[ -z "$WHEEL_PATH" || ! -f "$WHEEL_PATH" ]]; then
  echo "Wheel file not found in current directory or dist/: md2pdf_cli-*.whl" >&2
  exit 1
fi

apt-get update
apt-get install -y \
  python3 \
  python3-venv \
  python3-pip \
  libcairo2 \
  libpango-1.0-0 \
  libpangocairo-1.0-0 \
  libgdk-pixbuf-2.0-0 \
  libffi-dev \
  shared-mime-info \
  fonts-dejavu-core

mkdir -p "$INSTALL_DIR"
python3 -m venv "$INSTALL_DIR/.venv"

"$INSTALL_DIR/.venv/bin/pip" install -U pip
"$INSTALL_DIR/.venv/bin/pip" install "$WHEEL_PATH"

"$INSTALL_DIR/.venv/bin/md2pdf" --help >/dev/null

echo "Deploy success"
echo "Install dir: $INSTALL_DIR"
echo "Run HTTP server: $INSTALL_DIR/.venv/bin/md2pdf --serve --host 0.0.0.0 --port 20706"
