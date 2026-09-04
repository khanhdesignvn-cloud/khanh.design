import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CLI = ROOT / "backend" / "manage_course_portal.py"


def run_cli(folder, *args, stdin=""):
    return subprocess.run(
        [sys.executable, str(CLI), "--state-dir", str(folder), *args],
        input=stdin,
        capture_output=True,
        text=True,
        timeout=15,
        cwd=ROOT,
    )


def test_activate_uses_private_application_record_without_printing_phone():
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        app_id = "11111111-1111-4111-8111-111111111111"
        (folder / "applications.json").write_text(json.dumps([{"id": app_id, "full_name": "Nguyễn Văn An", "phone": "0912 345 678"}]))
        result = run_cli(folder, "activate", app_id, "--cohort", "2026-09")
        assert result.returncode == 0, result.stderr
        assert "Nguyễn Văn An" in result.stdout
        assert "0912" not in result.stdout
        stored = json.loads((folder / "students.json").read_text())
        assert stored[0]["id"] == app_id
        assert "phone" not in stored[0]
        assert "phone_hash" in stored[0]


def test_activate_rejects_unknown_application():
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        (folder / "applications.json").write_text("[]")
        result = run_cli(folder, "activate", "11111111-1111-4111-8111-111111111111")
        assert result.returncode != 0
        assert not (folder / "students.json").exists()


def test_configure_admin_reads_secret_from_stdin_and_never_echoes_it():
    with tempfile.TemporaryDirectory() as tmp:
        folder = Path(tmp)
        secret = "correct-horse-private-owner-key"
        result = run_cli(folder, "configure-admin", stdin=secret + "\n")
        assert result.returncode == 0, result.stderr
        assert secret not in result.stdout + result.stderr
        content = (folder / "admin-key.json").read_text()
        assert secret not in content
        assert '"hash"' in content
