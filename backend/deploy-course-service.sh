#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALL_DIR=/usr/local/lib/khanh-course
install -d -o root -g root -m 0755 "$INSTALL_DIR"
install -o root -g root -m 0644 "$ROOT/backend/course_application_server.py" "$INSTALL_DIR/course_application_server.py"
install -o root -g root -m 0644 "$ROOT/backend/course_learning_portal.py" "$INSTALL_DIR/course_learning_portal.py"
install -o root -g root -m 0755 "$ROOT/backend/manage_course_portal.py" "$INSTALL_DIR/manage_course_portal.py"
install -o root -g root -m 0644 "$ROOT/backend/systemd/khanh-course-application.service" /etc/systemd/system/khanh-course-application.service
install -o root -g root -m 0644 "$ROOT/backend/systemd/khanh-course-application-tunnel.service" /etc/systemd/system/khanh-course-application-tunnel.service
systemd-analyze verify /etc/systemd/system/khanh-course-application.service /etc/systemd/system/khanh-course-application-tunnel.service
systemctl daemon-reload
systemctl restart khanh-course-application.service
