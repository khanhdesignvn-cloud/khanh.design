from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
UNIT = ROOT / "backend" / "systemd" / "khanh-course-application.service"
DEPLOY = ROOT / "backend" / "deploy-course-service.sh"


def test_service_uses_private_state_and_non_root_identity():
    text = UNIT.read_text()
    assert "User=khanh-course" in text
    assert "Group=khanh-course" in text
    assert "StateDirectory=khanh-course" in text
    assert "--state-dir /var/lib/khanh-course" in text
    assert "ProtectSystem=strict" in text
    assert "UMask=0077" in text
    assert "admin" not in text.lower() or "admin-key" not in text.lower()


def test_deploy_installs_both_backend_modules_without_secrets():
    text = DEPLOY.read_text()
    assert "course_application_server.py" in text
    assert "course_learning_portal.py" in text
    assert "manage_course_portal.py" in text
    assert "systemd-analyze verify" in text
    assert "ADMIN_KEY" not in text
    assert "token-secret" not in text
