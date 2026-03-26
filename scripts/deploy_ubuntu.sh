#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${1:-$(pwd)}"
WHEEL_PATH=""

shopt -s nullglob
current_wheels=("$PWD"/md2pdf_cli-*.whl)
dist_wheels=("$PWD"/dist/md2pdf_cli-*.whl)
if [[ ${#current_wheels[@]} -gt 0 ]]; then
  IFS=$'\n' sorted=($(ls -1t "${current_wheels[@]}"))
  WHEEL_PATH="${sorted[0]}"
elif [[ ${#dist_wheels[@]} -gt 0 ]]; then
  IFS=$'\n' sorted=($(ls -1t "${dist_wheels[@]}"))
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
"$INSTALL_DIR/.venv/bin/pip" install --force-reinstall "$WHEEL_PATH"

"$INSTALL_DIR/.venv/bin/md2pdf" --help >/dev/null

SCRIPT_DIR="$INSTALL_DIR/scripts"
if [[ -x "$SCRIPT_DIR/stop_http_background.sh" || -f "$SCRIPT_DIR/stop_http_background.sh" ]]; then
  echo "Stopping old service..."
  bash "$SCRIPT_DIR/stop_http_background.sh" "$INSTALL_DIR" || true
fi

echo "Starting new service..."
bash "$SCRIPT_DIR/start_http_background.sh"

echo "Deploy success"
echo "Install dir: $INSTALL_DIR"
