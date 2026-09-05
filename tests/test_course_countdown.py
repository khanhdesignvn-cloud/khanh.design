import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "ai-learning"
HTML = SITE / "index.html"
JS = SITE / "app.js"
DEADLINE = "2026-09-15T23:59:00+07:00"


def run_node(expression):
    script = f"const app = require({json.dumps(str(JS))}); {expression}"
    return subprocess.run(["node", "-e", script], check=True, capture_output=True, text=True).stdout.strip()


def test_countdown_has_real_deadline_four_units_and_form_cta():
    html = HTML.read_text(encoding="utf-8")
    assert f'data-deadline="{DEADLINE}"' in html
    for part in ("days", "hours", "minutes", "seconds"):
        assert f'id="countdown-{part}"' in html
    assert 'class="countdown-cta btn" href="#apply"' in html
    assert "Đóng đăng ký lúc 23:59 ngày 15/09/2026" in html


def test_countdown_calculation_and_expiry_are_deterministic():
    active = run_node(
        "process.stdout.write(JSON.stringify(app.getCountdownParts("
        f"{json.dumps(DEADLINE)}, '2026-09-14T22:58:59+07:00')))"
    )
    assert json.loads(active) == {
        "days": 1,
        "hours": 1,
        "minutes": 0,
        "seconds": 1,
        "expired": False,
    }
    expired = run_node(
        "process.stdout.write(JSON.stringify(app.getCountdownParts("
        f"{json.dumps(DEADLINE)}, '2026-09-15T23:59:00+07:00')))"
    )
    assert json.loads(expired)["expired"] is True
