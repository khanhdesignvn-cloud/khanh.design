#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_DIR=/usr/local/lib/khanh-slide-admin
ENV_FILE=/etc/khanh-slide-admin/env
REPO_DIR=/srv/khanh.design
SERVICE=khanh-slide-admin.service

if [[ ${EUID} -ne 0 ]]; then
  printf 'Run as root.\n' >&2
  exit 1
fi
if [[ ! -f "$ENV_FILE" || -L "$ENV_FILE" ]]; then
  printf 'Create a regular %s with either SLIDE_ADMIN_PASSWORD_HASH or SLIDE_ADMIN_SETUP_ENABLED, owner root, mode 0600.\n' "$ENV_FILE" >&2
  exit 1
fi
if [[ "$(stat -c "%a" "$ENV_FILE")" != "600" ]]; then
  printf '%s must have mode 0600.\n' "$ENV_FILE" >&2
  exit 1
fi
if [[ "$(stat -c "%U:%G" "$ENV_FILE")" != "root:root" ]]; then
  printf '%s must be owned by root:root.\n' "$ENV_FILE" >&2
  exit 1
fi
if [[ ! -d "$REPO_DIR/.git" || ! -f "$REPO_DIR/100/slide-config.json" ]]; then
  printf '%s must be a deployment checkout with slide configuration.\n' "$REPO_DIR" >&2
  exit 1
fi
if ! getent passwd khanh-slide-admin >/dev/null; then
  useradd --system --home-dir /var/lib/khanh-slide-admin --shell /usr/sbin/nologin khanh-slide-admin
fi
python3 -c 'from PIL import Image' >/dev/null
install -d -o root -g root -m 0755 "$INSTALL_DIR"
install -o root -g root -m 0644 "$ROOT/backend/slide_admin.py" "$INSTALL_DIR/slide_admin.py"
install -o root -g root -m 0644 "$ROOT/backend/slide_admin_server.py" "$INSTALL_DIR/slide_admin_server.py"
install -o root -g root -m 0644 "$ROOT/backend/slide_publisher.py" "$INSTALL_DIR/slide_publisher.py"
install -o root -g root -m 0644 "$ROOT/backend/systemd/$SERVICE" "/etc/systemd/system/$SERVICE"
chown -R khanh-slide-admin:khanh-slide-admin "$REPO_DIR/.git" "$REPO_DIR/100"
systemd-analyze verify "/etc/systemd/system/$SERVICE"
systemctl daemon-reload
systemctl restart "$SERVICE"

health=''
for _ in {1..20}; do
  health="$(curl -fsS http://127.0.0.1:8093/health 2>/dev/null || true)"
  [[ "$health" == *'"status":"ok"'* ]] && exit 0
  sleep 0.25
done
printf 'Local health check failed.\n' >&2
exit 1