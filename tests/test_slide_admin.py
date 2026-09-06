import tempfile
import unittest
from io import BytesIO
from pathlib import Path

from PIL import Image

from backend.slide_admin import (
    PublishBusy,
    PublishLock,
    SessionStore,
    SlideValidationError,
    ensure_repo_path,
    hash_password,
    process_uploaded_image,
    sanitize_text,
    save_draft_atomic,
    validate_slide_config,
    verify_password,
)


class SlideAdminTests(unittest.TestCase):
    def test_password_hash_uses_random_scrypt_salt_and_verifies(self):
        first = hash_password("mật khẩu đủ dài")
        second = hash_password("mật khẩu đủ dài")
        self.assertNotEqual(first, second)
        self.assertTrue(first.startswith("scrypt$"))
        self.assertTrue(verify_password("mật khẩu đủ dài", first))
        self.assertFalse(verify_password("sai", first))
        self.assertFalse(verify_password("mật khẩu đủ dài", "invalid"))

    def test_sessions_expire_revoke_and_bind_csrf(self):
        now = [100.0]
        store = SessionStore(ttl_seconds=30, clock=lambda: now[0])
        token, csrf = store.create()
        self.assertTrue(store.validate(token, csrf))
        self.assertFalse(store.validate(token, "wrong"))
        now[0] = 131.0
        self.assertFalse(store.validate(token, csrf))

        token, csrf = store.create()
        store.revoke(token)
        self.assertFalse(store.validate(token, csrf))

    def test_config_validation_cleans_text_and_rejects_invalid_structure(self):
        base = ["base-one", "base-two"]
        config = {
            "schema_version": 1,
            "revision": "draft-1",
            "order": ["base-one", "custom-one", "base-two"],
            "hidden": ["base-two"],
            "overrides": {"base-one": {"title": "  Tiêu đề   mới  "}},
            "custom_slides": [{
                "id": "custom-one", "eyebrow": " Nhãn ", "title": "Tự hào Khe Sanh",
                "body": ["Một trăm năm cà phê."], "note": "Ghi chú",
                "image": "assets/admin/abc-123.webp",
            }],
        }
        cleaned = validate_slide_config(config, base)
        self.assertEqual("Tiêu đề mới", cleaned["overrides"]["base-one"]["title"])
        self.assertEqual("Nhãn", cleaned["custom_slides"][0]["eyebrow"])

        bad = dict(config, order=["base-one", "unknown", "base-two"])
        with self.assertRaises(SlideValidationError):
            validate_slide_config(bad, base)
        bad = dict(config, order=["base-one", "base-one", "base-two"])
        with self.assertRaises(SlideValidationError):
            validate_slide_config(bad, base)

    def test_text_sanitizer_removes_markup_and_limits_vietnamese_text(self):
        self.assertEqual("Xin chào thế giới", sanitize_text(" Xin <b>chào</b>   thế giới ", 40))
        with self.assertRaises(SlideValidationError):
            sanitize_text("đ" * 11, 10)

    def test_draft_save_is_atomic_private_and_replaceable(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "state" / "draft.json"
            save_draft_atomic(path, {"revision": "one"})
            self.assertEqual('{"revision":"one"}', path.read_text(encoding="utf-8"))
            self.assertEqual(0o600, path.stat().st_mode & 0o777)
            save_draft_atomic(path, {"revision": "two"})
            self.assertEqual('{"revision":"two"}', path.read_text(encoding="utf-8"))
            self.assertEqual([], list(path.parent.glob("*.tmp")))

    def test_publish_lock_rejects_overlapping_work(self):
        lock = PublishLock()
        with lock.acquire():
            with self.assertRaises(PublishBusy):
                with lock.acquire():
                    pass
        with lock.acquire():
            pass

    def test_repo_path_allows_only_files_below_100(self):
        with tempfile.TemporaryDirectory() as directory:
            repo = Path(directory)
            allowed = ensure_repo_path(repo, "100/assets/admin/image.webp")
            self.assertEqual(repo / "100/assets/admin/image.webp", allowed)
            for unsafe in ("README.md", "100/../README.md", "/etc/passwd", "100x/file"):
                with self.subTest(unsafe=unsafe), self.assertRaises(SlideValidationError):
                    ensure_repo_path(repo, unsafe)

    def test_uploaded_image_is_verified_resized_and_stripped(self):
        with tempfile.TemporaryDirectory() as directory:
            source = BytesIO()
            image = Image.new("RGB", (2000, 1000), "#a63d2f")
            image.getexif()[270] = "private metadata"
            image.save(source, "JPEG", exif=image.getexif())
            relative = process_uploaded_image(
                source.getvalue(), "image/jpeg", Path(directory) / "100/assets/admin"
            )
            self.assertRegex(relative, r"^assets/admin/[0-9a-f-]{36}\.webp$")
            saved = Path(directory) / "100" / relative
            self.assertTrue(saved.exists())
            with Image.open(saved) as result:
                self.assertEqual((1600, 800), result.size)
                self.assertEqual("WEBP", result.format)
                self.assertFalse(result.getexif())

    def test_uploaded_image_rejects_fake_mime_broken_and_oversized_input(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "100/assets/admin"
            png = BytesIO()
            Image.new("RGB", (20, 20)).save(png, "PNG")
            with self.assertRaises(SlideValidationError):
                process_uploaded_image(png.getvalue(), "image/jpeg", target)
            with self.assertRaises(SlideValidationError):
                process_uploaded_image(b"not an image", "image/png", target)
            with self.assertRaises(SlideValidationError):
                process_uploaded_image(b"x" * 101, "image/png", target, max_bytes=100)

    def test_uploaded_image_rejects_excessive_pixels(self):
        with tempfile.TemporaryDirectory() as directory:
            source = BytesIO()
            Image.new("RGB", (101, 101)).save(source, "WEBP")
            with self.assertRaises(SlideValidationError):
                process_uploaded_image(
                    source.getvalue(), "image/webp", Path(directory), max_pixels=10_000
                )


if __name__ == "__main__":
    unittest.main()
