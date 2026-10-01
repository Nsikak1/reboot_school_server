#!/usr/bin/env bash
set -e

SRC_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DEST="/opt/school-server"
SERVICE_NAME="school.service"

if [ "$EUID" -ne 0 ]; then
  echo "This script must be run as root. Re-running with sudo..."
    exec sudo "$0" "$@"
fi

echo "==> Syncing code to $DEST..."
sudo rsync -av --delete \
  --exclude='venv/' \
  --exclude='deploy.sh' \
  --exclude='.venv/' \
  --exclude='__pycache__/' \
  --exclude='.git/' \
  --exclude='.env' \
  "$SRC_DIR/" "$DEST/"


echo "==> Ensuring correct group ownership..."
sudo chown -R root:devgrp "$DEST"
sudo chmod -R 775 "$DEST"

echo "==> Restarting systemd service..."
sudo systemctl restart "$SERVICE_NAME"

echo "==> Deployment complete!"
systemctl status "$SERVICE_NAME" --no-pager