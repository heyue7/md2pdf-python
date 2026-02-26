#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
INSTALL_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
HOST="${MD2PDF_HOST:-0.0.0.0}"
PORT="${MD2PDF_PORT:-20706}"
LOG_FILE="${MD2PDF_LOG_FILE:-$INSTALL_DIR/md2pdf-http.log}"
PID_FILE="${MD2PDF_PID_FILE:-$INSTALL_DIR/md2pdf-http.pid}"

BIN_PATH="$INSTALL_DIR/.venv/bin/md2pdf"

if [[ ! -x "$BIN_PATH" ]]; then
  echo "md2pdf binary not found: $BIN_PATH" >&2
  exit 1
fi

if [[ -f "$PID_FILE" ]]; then
  OLD_PID="$(cat "$PID_FILE")"
  if [[ -n "$OLD_PID" ]] && kill -0 "$OLD_PID" 2>/dev/null; then
    echo "Service already running, pid=$OLD_PID"
    exit 0
  fi
fi

mkdir -p "$(dirname "$LOG_FILE")"
nohup "$BIN_PATH" --serve --host "$HOST" --port "$PORT" >"$LOG_FILE" 2>&1 &
NEW_PID="$!"
echo "$NEW_PID" >"$PID_FILE"

sleep 1
if kill -0 "$NEW_PID" 2>/dev/null; then
  echo "Service started, pid=$NEW_PID"
  echo "Log: $LOG_FILE"
  echo "PID file: $PID_FILE"
  exit 0
fi

echo "Service failed to start. Check log: $LOG_FILE" >&2
exit 1
