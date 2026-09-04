from html.parser import HTMLParser
from pathlib import Path
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "ai-van-hanh-doanh-nghiep"
HTML = SITE / "index.html"
JS = SITE / "app.js"


class FormParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.fields = {}
        self.labels = set()
        self.forms = []
        self.in_application_form = False

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.forms.append(attrs)
            self.in_application_form = attrs.get("id") == "course-application"
        if not self.in_application_form:
            return
        if tag == "label" and attrs.get("for"):
            self.labels.add(attrs["for"])
        if tag in {"input", "select", "textarea"} and attrs.get("name"):
            self.fields[attrs["name"]] = attrs

    def handle_endtag(self, tag):
        if tag == "form":
            self.in_application_form = False


def parse_form():
    parser = FormParser()
    parser.feed(HTML.read_text(encoding="utf-8"))
    return parser


def run_node(expression):
    script = f"const app = require({json.dumps(str(JS))}); {expression}"
    return subprocess.run(
        ["node", "-e", script],
        check=True,
        capture_output=True,
        text=True,
    ).stdout.strip()


def test_application_collects_only_declared_required_fields_with_labels():
    form = parse_form()
    required = {
        "full_name",
        "phone",
        "email",
        "industry",
        "role",
        "challenge",
        "commitment",
        "data_consent",
    }
    assert required == set(form.fields)
    assert all("required" in form.fields[name] for name in required)
    assert {attrs["id"] for attrs in form.fields.values()} <= form.labels
    assert len(form.forms) == 1
    assert {key: form.forms[0][key] for key in ("id", "action", "method", "enctype")} == {
        "id": "course-application",
        "action": "mailto:hi@nguyenquockhanh.vn",
        "method": "post",
        "enctype": "text/plain",
    }


def test_draft_storage_is_explicitly_gated_by_data_consent():
    source = JS.read_text(encoding="utf-8")
    assert "localStorage.setItem" in source
    assert "localStorage.removeItem" in source
    assert "data_consent" in source
    assert run_node("process.stdout.write(String(app.canPersistDraft(false)))") == "false"
    assert run_node("process.stdout.write(String(app.canPersistDraft(true)))") == "true"


def test_email_fallback_is_encoded_and_requires_user_to_send():
    output = run_node(
        "process.stdout.write(app.buildMailto({"
        "full_name:'Nguyễn An',phone:'0900 000 000',email:'an@example.com',"
        "industry:'Dịch vụ',role:'Chủ doanh nghiệp',challenge:'Chuẩn hóa CSKH'"
        "}))"
    )
    assert output.startswith("mailto:hi@nguyenquockhanh.vn?")
    assert "subject=" in output and "body=" in output
    assert "Nguy%E1%BB%85n%20An" in output
    assert "\n" not in output and "\r" not in output
    html = HTML.read_text(encoding="utf-8")
    assert "tự xác nhận gửi" in html


def test_user_data_is_rendered_and_handled_without_unsafe_sinks_or_logging():
    source = JS.read_text(encoding="utf-8")
    assert ".textContent" in source
    assert "innerHTML" not in source
    assert "console.log" not in source
    assert "encodeURIComponent" in source
    assert "fetch(" not in source
