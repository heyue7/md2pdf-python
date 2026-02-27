#!/usr/bin/env bash
set -euo pipefail

if [[ $# -ne 1 ]]; then
  echo "Usage: $0 <user[:password]@ip:remote_dir | alias:remote_dir>" >&2
  exit 1
fi

TARGET="$1"
PASSWORD=""
REMOTE=""
REMOTE_DIR=""

if [[ "$TARGET" =~ ^([^@]+)@([^:]+):(.+)$ ]]; then
  AUTH="${BASH_REMATCH[1]}"
  HOST="${BASH_REMATCH[2]}"
  REMOTE_DIR="${BASH_REMATCH[3]}"

  USER_NAME="$AUTH"
  if [[ "$AUTH" == *:* ]]; then
    USER_NAME="${AUTH%%:*}"
    PASSWORD="${AUTH#*:}"
  fi

  if [[ -z "$USER_NAME" || -z "$HOST" || -z "$REMOTE_DIR" ]]; then
    echo "Invalid target content. user, host and remote_dir are required." >&2
    exit 1
  fi
  REMOTE="$USER_NAME@$HOST"
elif [[ "$TARGET" =~ ^([^:]+):(.+)$ ]]; then
  ALIAS="${BASH_REMATCH[1]}"
  REMOTE_DIR="${BASH_REMATCH[2]}"
  if [[ -z "$ALIAS" || -z "$REMOTE_DIR" ]]; then
    echo "Invalid target content. alias and remote_dir are required." >&2
    exit 1
  fi
  REMOTE="$ALIAS"
else
  echo "Invalid target format. Expected: user[:password]@ip:remote_dir or alias:remote_dir" >&2
  exit 1
fi

shopt -s nullglob
WHEELS=("$PWD"/md2pdf_cli-*.whl "$PWD"/dist/md2pdf_cli-*.whl)
shopt -u nullglob

if [[ ${#WHEELS[@]} -eq 0 ]]; then
  echo "No wheel found. Build first: python -m build" >&2
  exit 1
fi

LATEST_WHEEL=""
for wheel in "${WHEELS[@]}"; do
  if [[ -z "$LATEST_WHEEL" || "$wheel" -nt "$LATEST_WHEEL" ]]; then
    LATEST_WHEEL="$wheel"
  fi
done

for f in \
  "$LATEST_WHEEL" \
  "$PWD/scripts/deploy_ubuntu.sh" \
  "$PWD/scripts/deploy_rhel.sh" \
  "$PWD/scripts/start_http_background.sh" \
  "$PWD/scripts/stop_http_background.sh" \
  "$PWD/scripts/convert_with_watermark.sh"; do
  if [[ ! -f "$f" ]]; then
    echo "Required file missing: $f" >&2
    exit 1
  fi
done

TMP_DIR="$(mktemp -d)"
trap 'rm -rf "$TMP_DIR"' EXIT

PKG_DIR="$TMP_DIR/md2pdf_bundle"
mkdir -p "$PKG_DIR/scripts"

cp "$LATEST_WHEEL" "$PKG_DIR/"
cp "$PWD/scripts/deploy_ubuntu.sh" "$PKG_DIR/scripts/"
cp "$PWD/scripts/deploy_rhel.sh" "$PKG_DIR/scripts/"
cp "$PWD/scripts/start_http_background.sh" "$PKG_DIR/scripts/"
cp "$PWD/scripts/stop_http_background.sh" "$PKG_DIR/scripts/"
cp "$PWD/scripts/convert_with_watermark.sh" "$PKG_DIR/scripts/"

BUNDLE_NAME="md2pdf_deploy_bundle_$(date +%Y%m%d_%H%M%S).tar.gz"
BUNDLE_PATH="$TMP_DIR/$BUNDLE_NAME"
tar -C "$PKG_DIR" -czf "$BUNDLE_PATH" .

SSH_OPTS=(-o StrictHostKeyChecking=accept-new)

if [[ -n "${MD2PDF_SSH_KEY:-}" ]]; then
  SSH_OPTS+=( -i "$MD2PDF_SSH_KEY" )
fi

if [[ -n "$PASSWORD" ]]; then
  if ! command -v sshpass >/dev/null 2>&1; then
    echo "Password mode needs sshpass installed." >&2
    exit 1
  fi

  if SSHPASS="$PASSWORD" sshpass -e scp "${SSH_OPTS[@]}" "$BUNDLE_PATH" "$REMOTE:$REMOTE_DIR/"; then
    :
  else
    SSHPASS="$PASSWORD" sshpass -e ssh "${SSH_OPTS[@]}" "$REMOTE" "mkdir -p \"$REMOTE_DIR\""
    SSHPASS="$PASSWORD" sshpass -e scp "${SSH_OPTS[@]}" "$BUNDLE_PATH" "$REMOTE:$REMOTE_DIR/"
  fi
else
  if scp "${SSH_OPTS[@]}" "$BUNDLE_PATH" "$REMOTE:$REMOTE_DIR/"; then
    :
  else
    ssh "${SSH_OPTS[@]}" "$REMOTE" "mkdir -p \"$REMOTE_DIR\""
    scp "${SSH_OPTS[@]}" "$BUNDLE_PATH" "$REMOTE:$REMOTE_DIR/"
  fi
fi

echo "Upload success"
echo "Remote: $REMOTE:$REMOTE_DIR/$BUNDLE_NAME"
echo "Then run on server:"
echo "  cd $REMOTE_DIR"
echo "  tar -xzf $BUNDLE_NAME"
echo "  sudo bash scripts/deploy_ubuntu.sh"
