#!/usr/bin/env python3
"""Create the founding-cohort Google Form from an approved JSON spec."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
from typing import Any

DEFAULT_MAPPING = Path.home() / ".hermes" / "course-ai-google-form.json"
TOKEN = Path.home() / ".hermes" / "google_token.json"


def normalize_spec(spec: dict[str, Any]) -> dict[str, Any]:
    if "questions" in spec:
        return spec
    fields = spec.get("fields")
    if not isinstance(fields, list) or not fields:
        raise ValueError("fields must be a non-empty list")
    type_map = {
        "short_text": "text",
        "email": "text",
        "paragraph": "paragraph",
        "single_choice": "radio",
        "checkbox": "checkbox",
    }
    questions = []
    for field in fields:
        source_type = field.get("type")
        if source_type not in type_map:
            raise ValueError(f"unsupported field type: {source_type}")
        question = {
            "title": field.get("label", ""),
            "type": type_map[source_type],
            "required": bool(field.get("required", False)),
        }
        if field.get("help"):
            question["description"] = field["help"]
        if source_type == "single_choice":
            question["options"] = field.get("options", [])
        elif source_type == "checkbox":
            question["options"] = field.get("options") or [str(field.get("label", "Tôi đồng ý"))]
        questions.append(question)
    return {**spec, "questions": questions}


def _question(spec: dict[str, Any]) -> dict[str, Any]:
    qtype = spec.get("type")
    base: dict[str, Any] = {"required": bool(spec.get("required", False))}
    if qtype in {"text", "paragraph"}:
        base["textQuestion"] = {"paragraph": qtype == "paragraph"}
    elif qtype in {"radio", "checkbox", "dropdown"}:
        options = spec.get("options")
        if not isinstance(options, list) or not options or not all(isinstance(x, str) and x.strip() for x in options):
            raise ValueError(f"{spec.get('title', 'question')}: choice options required")
        type_map = {"radio": "RADIO", "checkbox": "CHECKBOX", "dropdown": "DROP_DOWN"}
        base["choiceQuestion"] = {
            "type": type_map[qtype],
            "options": [{"value": x.strip()} for x in options],
            "shuffle": False,
        }
    else:
        raise ValueError(f"unsupported question type: {qtype}")
    return base


def build_item_requests(spec: dict[str, Any]) -> list[dict[str, Any]]:
    questions = spec.get("questions")
    if not isinstance(questions, list) or not questions:
        raise ValueError("questions must be a non-empty list")
    requests = []
    for index, item in enumerate(questions):
        title = str(item.get("title", "")).strip()
        if not title:
            raise ValueError("question title is required")
        form_item: dict[str, Any] = {
            "title": title,
            "questionItem": {"question": _question(item)},
        }
        if item.get("description"):
            form_item["description"] = str(item["description"]).strip()
        requests.append({"createItem": {"item": form_item, "location": {"index": index}}})
    return requests


def publish_body() -> dict[str, Any]:
    return {
        "publishSettings": {"publishState": {"isPublished": True, "isAcceptingResponses": True}},
        "updateMask": "publish_state",
    }


def _save_mapping(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temp = path.with_suffix(".tmp")
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.chmod(temp, 0o600)
    temp.replace(path)


def create_form(spec_path: Path, mapping_path: Path = DEFAULT_MAPPING) -> dict[str, Any]:
    from google.oauth2.credentials import Credentials
    from googleapiclient.discovery import build

    spec = normalize_spec(json.loads(spec_path.read_text(encoding="utf-8")))
    title = str(spec.get("title", "")).strip()
    if not title:
        raise ValueError("form title is required")
    requests = build_item_requests(spec)
    creds = Credentials.from_authorized_user_file(str(TOKEN))
    forms = build("forms", "v1", credentials=creds, cache_discovery=False)
    drive = build("drive", "v3", credentials=creds, cache_discovery=False)

    if mapping_path.exists():
        mapping = json.loads(mapping_path.read_text(encoding="utf-8"))
        current = forms.forms().get(formId=mapping["form_id"]).execute()
        if current.get("info", {}).get("title") != title:
            raise RuntimeError("mapped form title does not match approved spec")
        return {
            **mapping,
            "responder_uri": current.get("responderUri", mapping.get("responder_uri", "")),
            "reused": True,
            "item_count": len(current.get("items", [])),
        }

    created = forms.forms().create(body={"info": {"title": title, "documentTitle": title}}).execute()
    form_id = created["formId"]
    mapping = {"form_id": form_id, "title": title, "state": "created"}
    _save_mapping(mapping_path, mapping)
    try:
        forms.forms().batchUpdate(formId=form_id, body={"requests": requests}).execute()
        forms.forms().setPublishSettings(formId=form_id, body=publish_body()).execute()
        parent = str(spec.get("drive_parent_id", "")).strip()
        if parent:
            current = drive.files().get(fileId=form_id, fields="parents").execute().get("parents", [])
            drive.files().update(
                fileId=form_id,
                addParents=parent,
                removeParents=",".join(current) if current else None,
                fields="id,parents",
            ).execute()
            check = drive.files().get(fileId=form_id, fields="id,parents,trashed").execute()
            if parent not in check.get("parents", []) or check.get("trashed"):
                raise RuntimeError("form Drive parent verification failed")
        final = forms.forms().get(formId=form_id).execute()
        if len(final.get("items", [])) != len(requests):
            raise RuntimeError("form item count verification failed")
        mapping.update({
            "state": "published",
            "responder_uri": final.get("responderUri", ""),
            "edit_uri": f"https://docs.google.com/forms/d/{form_id}/edit",
            "item_count": len(requests),
        })
        _save_mapping(mapping_path, mapping)
        return {**mapping, "reused": False}
    except Exception:
        mapping["state"] = "incomplete"
        _save_mapping(mapping_path, mapping)
        raise


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("spec", type=Path)
    parser.add_argument("--mapping", type=Path, default=DEFAULT_MAPPING)
    args = parser.parse_args()
    result = create_form(args.spec, args.mapping)
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
