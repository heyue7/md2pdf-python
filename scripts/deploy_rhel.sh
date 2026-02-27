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

dnf install -y \
  python3 \
  python3-pip \
  python3-devel \
  cairo \
  pango \
  gdk-pixbuf2 \
  libffi \
  shared-mime-info \
  dejavu-sans-fonts

mkdir -p "$INSTALL_DIR"
python3 -m venv "$INSTALL_DIR/.venv"

"$INSTALL_DIR/.venv/bin/pip" install -U pip
"$INSTALL_DIR/.venv/bin/pip" install --force-reinstall "$WHEEL_PATH"

"$INSTALL_DIR/.venv/bin/md2pdf" --help >/dev/null

echo "Deploy success"
echo "Install dir: $INSTALL_DIR"
echo "Run HTTP server: $INSTALL_DIR/.venv/bin/md2pdf --serve --host 0.0.0.0 --port 20706"
echo "Or run in background: bash $INSTALL_DIR/scripts/start_http_background.sh"
