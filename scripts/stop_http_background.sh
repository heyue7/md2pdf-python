#!/usr/bin/env bash
set -euo pipefail

INSTALL_DIR="${1:-$(pwd)}"
PID_FILE="${2:-$INSTALL_DIR/md2pdf-http.pid}"

_kill_and_wait() {
  local pid="$1"
  if ! kill -0 "$pid" 2>/dev/null; then
    echo "Process $pid not running"
    return 0
  fi
  kill "$pid"
  for _ in {1..20}; do
    if ! kill -0 "$pid" 2>/dev/null; then
      echo "Service stopped, pid=$pid"
      return 0
    fi
    sleep 0.2
  done
  kill -9 "$pid" 2>/dev/null || true
  echo "Service forced to stop, pid=$pid"
}

FOUND_PID=""

if [[ -f "$PID_FILE" ]]; then
  FOUND_PID="$(cat "$PID_FILE")"
  rm -f "$PID_FILE"
  if [[ -n "$FOUND_PID" ]] && kill -0 "$FOUND_PID" 2>/dev/null; then
    _kill_and_wait "$FOUND_PID"
  else
    FOUND_PID=""
  fi
fi

PIDS="$(pgrep -f 'md2pdf --serve' 2>/dev/null || true)"
if [[ -n "$PIDS" ]]; then
  while IFS= read -r pid; do
    [[ "$pid" == "$FOUND_PID" ]] && continue
    echo "Found orphan md2pdf process, pid=$pid"
    _kill_and_wait "$pid"
  done <<< "$PIDS"
elif [[ -z "$FOUND_PID" ]]; then
  echo "No md2pdf service running"
fi
