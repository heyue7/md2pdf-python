#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${1:-$(pwd)}"
PID_FILE="${2:-$INSTALL_DIR/md2pdf-http.pid}"

if [[ ! -f "$PID_FILE" ]]; then
  echo "PID file not found: $PID_FILE"
  exit 0
fi

PID="$(cat "$PID_FILE")"
if [[ -z "$PID" ]]; then
  rm -f "$PID_FILE"
  echo "PID file was empty and has been removed"
  exit 0
fi

if ! kill -0 "$PID" 2>/dev/null; then
  rm -f "$PID_FILE"
  echo "Process not running, cleaned PID file"
  exit 0
fi

kill "$PID"

for _ in {1..20}; do
  if ! kill -0 "$PID" 2>/dev/null; then
    rm -f "$PID_FILE"
    echo "Service stopped, pid=$PID"
    exit 0
  fi
  sleep 0.2
done

kill -9 "$PID" 2>/dev/null || true
rm -f "$PID_FILE"
echo "Service forced to stop, pid=$PID"
