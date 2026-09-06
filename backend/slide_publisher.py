"""Git-backed publisher for slide configuration and admin images."""

from __future__ import annotations

import json
import subprocess
import threading
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

try:
    from backend.slide_admin import PublishLock, SlideValidationError, ensure_repo_path, save_draft_atomic
except ModuleNotFoundError:  # Installed modules live side by side.
    from slide_admin import PublishLock, SlideValidationError, ensure_repo_path, save_draft_atomic  # type: ignore[no-redef]


DEPLOYMENT_STATES = frozenset({"queued", "building", "success", "failure"})


class SlidePublisher:
    def __init__(self, repo_root: str | Path, ledger_path: str | Path, *, remote: str = "origin"):
        self.repo_root = Path(repo_root).resolve()
        self.ledger_path = Path(ledger_path)
        self.remote = remote
        self.lock = PublishLock()
        self._ledger_lock = threading.Lock()

    def _git(self, *args: str, check: bool = True) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            ["git", *args], cwd=self.repo_root, check=check,
            capture_output=True, text=True,
        )

    def _read_ledger(self) -> list[dict[str, Any]]:
        if not self.ledger_path.exists():
            return []
        value = json.loads(self.ledger_path.read_text(encoding="utf-8"))
        if not isinstance(value, list):
            raise ValueError("invalid deployment ledger")
        return value

    def _write_ledger(self, entries: list[dict[str, Any]]) -> None:
        save_draft_atomic(self.ledger_path, entries)

    def create_deployment(
        self,
        revision: str,
        *,
        action: str = "publish",
        previous_config: dict | None = None,
        config: dict | None = None,
        commit: str | None = None,
    ) -> dict[str, Any]:
        entry = {
            "id": str(uuid.uuid4()),
            "revision": revision,
            "action": action,
            "state": "queued",
            "commit": commit,
            "created_at": datetime.now(timezone.utc).isoformat(),
        }
        if previous_config is not None:
            entry["previous_config"] = previous_config
        if config is not None:
            entry["config"] = config
        with self._ledger_lock:
            entries = self._read_ledger()
            entries.append(entry)
            self._write_ledger(entries)
        return dict(entry)

    def deployment(self, deployment_id: str) -> dict[str, Any]:
        with self._ledger_lock:
            for entry in self._read_ledger():
                if entry.get("id") == deployment_id:
                    return self._public_entry(entry)
        raise KeyError(deployment_id)

    def set_deployment_state(self, deployment_id: str, state: str) -> dict[str, Any]:
        if state not in DEPLOYMENT_STATES:
            raise ValueError("invalid deployment state")
        with self._ledger_lock:
            entries = self._read_ledger()
            for entry in entries:
                if entry.get("id") == deployment_id:
                    entry["state"] = state
                    entry["updated_at"] = datetime.now(timezone.utc).isoformat()
                    self._write_ledger(entries)
                    return self._public_entry(entry)
        raise KeyError(deployment_id)

    @staticmethod
    def _public_entry(entry: dict[str, Any]) -> dict[str, Any]:
        return {key: value for key, value in entry.items() if key not in {"previous_config", "config"}}

    def publish(self, config: dict) -> dict[str, Any]:
        with self.lock.acquire():
            return self._commit_config(config, action="publish")

    def _commit_config(self, config: dict, *, action: str, previous_config: dict | None = None) -> dict[str, Any]:
        config_path = ensure_repo_path(self.repo_root, "100/slide-config.json")
        current = json.loads(config_path.read_text(encoding="utf-8"))
        if previous_config is None:
            previous_config = current
        if current == config:
            return {
                "id": None,
                "revision": config.get("revision", ""),
                "state": "unchanged",
                "commit": self._git("rev-parse", "HEAD").stdout.strip(),
            }
        save_draft_atomic(config_path, config)

        paths = ["100/slide-config.json"]
        for slide in config.get("custom_slides", []):
            image = slide.get("image", "") if isinstance(slide, dict) else ""
            if image:
                relative = f"100/{image}"
                source = ensure_repo_path(self.repo_root, relative)
                if not source.is_file():
                    raise SlideValidationError("referenced image does not exist")
                paths.append(relative)

        staged_before = self._git("diff", "--cached", "--name-only").stdout.splitlines()
        if staged_before:
            raise RuntimeError("git index must be clean before publishing")
        self._git("add", "--", *sorted(set(paths)))
        if self._git("diff", "--cached", "--quiet", check=False).returncode == 0:
            return {"id": None, "revision": config.get("revision", ""), "state": "unchanged", "commit": self._git("rev-parse", "HEAD").stdout.strip()}

        message = (
            f"Hoàn tác slide về {config.get('revision', 'revision')}"
            if action == "rollback"
            else f"Xuất bản slide {config.get('revision', 'revision')}"
        )
        self._git("commit", "-m", message)
        commit = self._git("rev-parse", "HEAD").stdout.strip()
        entry = self.create_deployment(
            str(config.get("revision", "")), action=action,
            previous_config=previous_config, config=config, commit=commit,
        )
        pushed = self._git("push", self.remote, "HEAD:main", check=False)
        if pushed.returncode != 0:
            failed = self.set_deployment_state(entry["id"], "failure")
            failed["error"] = "push_failed"
            return failed
        return self._public_entry(entry)

    def rollback(self) -> dict[str, Any]:
        with self.lock.acquire():
            with self._ledger_lock:
                entries = self._read_ledger()
            candidates = [entry for entry in entries if entry.get("action") == "publish" and entry.get("state") != "failure"]
            if not candidates or "previous_config" not in candidates[-1]:
                raise ValueError("no published revision to roll back")
            target = candidates[-1]["previous_config"]
            current_path = ensure_repo_path(self.repo_root, "100/slide-config.json")
            current = json.loads(current_path.read_text(encoding="utf-8"))
            return self._commit_config(target, action="rollback", previous_config=current)
