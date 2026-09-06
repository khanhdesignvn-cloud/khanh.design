import os
import stat
import unittest
from pathlib import Path

from backend.slide_admin_server import resolve_auth_state, resolve_password_hash


ROOT = Path(__file__).resolve().parents[1]
UNIT = ROOT / "backend/systemd/khanh-slide-admin.service"
DEPLOY = ROOT / "backend/deploy-slide-admin.sh"
APP = ROOT / "100/admin/app.js"


class SlideAdminDeploymentTests(unittest.TestCase):
    def test_service_is_loopback_only_hardened_and_uses_private_credentials(self):
        text = UNIT.read_text(encoding="utf-8")
        self.assertIn("User=khanh-slide-admin", text)
        self.assertIn("Group=khanh-slide-admin", text)
        self.assertIn("EnvironmentFile=/etc/khanh-slide-admin/env", text)
        self.assertIn("SLIDE_ADMIN_SETUP_ENABLED", text)
        self.assertIn("SLIDE_ADMIN_PASSWORD_HASH", text)
        self.assertIn("--host 127.0.0.1 --port 8093", text)
        self.assertNotIn("--password-hash", text)
        for directive in (
            "ProtectSystem=strict",
            "ProtectHome=true",
            "NoNewPrivileges=true",
            "UMask=0077",
            "RestrictAddressFamilies=AF_INET AF_INET6 AF_UNIX",
        ):
            self.assertIn(directive, text)
        writable = next(line for line in text.splitlines() if line.startswith("ReadWritePaths="))
        self.assertEqual(
            "ReadWritePaths=/var/lib/khanh-slide-admin /srv/khanh.design/.git /srv/khanh.design/100",
            writable,
        )

    def test_server_reads_password_hash_from_environment_without_echoing_it(self):
        self.assertEqual("hash-value", resolve_password_hash("", {"SLIDE_ADMIN_PASSWORD_HASH": "hash-value"}))
        self.assertEqual("explicit", resolve_password_hash("explicit", {"SLIDE_ADMIN_PASSWORD_HASH": "hash-value"}))
        with self.assertRaises(ValueError):
            resolve_password_hash("", {})

    def test_startup_allows_passwordless_mode_only_for_exact_setup_flag(self):
        import tempfile

        with tempfile.TemporaryDirectory() as directory:
            state = Path(directory)
            self.assertEqual(("", True, state / "password.hash"), resolve_auth_state(state, "", {"SLIDE_ADMIN_SETUP_ENABLED": "1"}))
            for environment in ({}, {"SLIDE_ADMIN_SETUP_ENABLED": "true"}, {"SLIDE_ADMIN_SETUP_ENABLED": "0"}):
                with self.assertRaises(ValueError):
                    resolve_auth_state(state, "", environment)
            (state / "password.hash").write_text("stored-hash", encoding="utf-8")
            self.assertEqual(("stored-hash", False, state / "password.hash"), resolve_auth_state(state, "", {"SLIDE_ADMIN_SETUP_ENABLED": "1"}))

    def test_deploy_script_installs_files_checks_env_permissions_and_health(self):
        text = DEPLOY.read_text(encoding="utf-8")
        for filename in ("slide_admin.py", "slide_admin_server.py", "slide_publisher.py"):
            self.assertIn(filename, text)
        self.assertIn("/etc/khanh-slide-admin/env", text)
        self.assertIn('stat -c "%a"', text)
        self.assertIn('stat -c "%U:%G"', text)
        self.assertIn("root:root", text)
        self.assertIn("600", text)
        self.assertIn("SLIDE_ADMIN_SETUP_ENABLED", text)
        self.assertIn("systemd-analyze verify", text)
        self.assertIn("http://127.0.0.1:8093/health", text)
        self.assertIn('"status":"ok"', text)
        self.assertNotIn("set -x", text)
        self.assertNotIn("SLIDE_ADMIN_PASSWORD_HASH=", text)
        self.assertNotIn("SLIDE_ADMIN_SETUP_ENABLED=", text)
        self.assertFalse(bool(os.stat(DEPLOY).st_mode & stat.S_IWOTH))

    def test_systemd_does_not_embed_setup_or_password_values(self):
        text = UNIT.read_text(encoding="utf-8")
        self.assertNotIn("Environment=SLIDE_ADMIN_PASSWORD_HASH", text)
        self.assertNotIn("Environment=SLIDE_ADMIN_SETUP_ENABLED", text)

    def test_frontend_uses_stable_https_api_path(self):
        text = APP.read_text(encoding="utf-8")
        self.assertIn('"https://quockhanh.tino.page/slide-admin-api"', text)
        self.assertNotIn("trycloudflare.com", text)
        self.assertNotIn("http://", text)


if __name__ == "__main__":
    unittest.main()
