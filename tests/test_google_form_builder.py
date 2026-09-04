import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "course" / "scripts"))

from create_google_form import build_item_requests, normalize_spec, publish_body  # noqa: E402


def test_build_item_requests_preserves_order_and_required_fields():
    spec = {
        "questions": [
            {"title": "Họ và tên", "type": "text", "required": True},
            {"title": "Vấn đề muốn giải quyết", "type": "paragraph", "required": True},
            {"title": "Vai trò", "type": "radio", "required": True, "options": ["Chủ doanh nghiệp", "Marketing"]},
            {"title": "Đồng ý", "type": "checkbox", "required": True, "options": ["Tôi đồng ý"]},
        ]
    }
    requests = build_item_requests(spec)
    assert [r["createItem"]["item"]["title"] for r in requests] == [
        "Họ và tên", "Vấn đề muốn giải quyết", "Vai trò", "Đồng ý"
    ]
    assert [r["createItem"]["location"]["index"] for r in requests] == [0, 1, 2, 3]
    first = requests[0]["createItem"]["item"]["questionItem"]["question"]
    second = requests[1]["createItem"]["item"]["questionItem"]["question"]
    assert first["required"] is True and first["textQuestion"]["paragraph"] is False
    assert second["textQuestion"]["paragraph"] is True
    assert requests[2]["createItem"]["item"]["questionItem"]["question"]["choiceQuestion"]["type"] == "RADIO"
    assert requests[3]["createItem"]["item"]["questionItem"]["question"]["choiceQuestion"]["type"] == "CHECKBOX"


def test_unknown_question_type_is_rejected():
    try:
        build_item_requests({"questions": [{"title": "X", "type": "secret", "required": True}]})
    except ValueError as exc:
        assert "unsupported question type" in str(exc)
    else:
        raise AssertionError("unsupported type was accepted")


def test_normalize_approved_application_spec():
    approved = {
        "title": "Đăng ký cohort",
        "description": "Mô tả",
        "fields": [
            {"id": "name", "label": "Họ và tên", "type": "short_text", "required": True},
            {"id": "role", "label": "Vai trò", "type": "single_choice", "required": True, "options": ["Chủ doanh nghiệp"]},
            {"id": "consent", "label": "Tôi đồng ý", "type": "checkbox", "required": True},
        ],
    }
    normalized = normalize_spec(approved)
    assert normalized["questions"][0]["type"] == "text"
    assert normalized["questions"][1]["type"] == "radio"
    assert normalized["questions"][2]["options"] == ["Tôi đồng ý"]
    assert normalized["description"] == "Mô tả"


def test_publish_body_sets_both_required_state_fields():
    assert publish_body() == {
        "publishSettings": {"publishState": {"isPublished": True, "isAcceptingResponses": True}},
        "updateMask": "publish_state",
    }
