#!/usr/bin/env python3
"""Private operator CLI for the course learning portal."""
from __future__ import annotations

import argparse
import getpass
import json
import sys
from pathlib import Path

try:
    from backend.course_learning_portal import CourseLearningPortal
except ModuleNotFoundError:
    from course_learning_portal import CourseLearningPortal


def portal_for(state_dir: Path) -> CourseLearningPortal:
    return CourseLearningPortal(
        students_path=state_dir / "students.json",
        submissions_path=state_dir / "submissions.json",
        token_secret_path=state_dir / "portal-token-secret",
        admin_key_path=state_dir / "admin-key.json",
    )


def main() -> int:
    parser = argparse.ArgumentParser(description="Manage the private course portal")
    parser.add_argument("--state-dir", type=Path, default=Path("/var/lib/khanh-course"))
    commands = parser.add_subparsers(dest="command", required=True)
    activate = commands.add_parser("activate")
    activate.add_argument("application_id")
    activate.add_argument("--cohort", default="2026-09")
    commands.add_parser("configure-admin")
    commands.add_parser("list-students")
    args = parser.parse_args()
    portal = portal_for(args.state_dir)

    if args.command == "configure-admin":
        key = getpass.getpass("Khóa quản trị mới: ") if sys.stdin.isatty() else sys.stdin.readline().rstrip("\n")
        portal.configure_admin(key)
        print("Đã cấu hình khóa quản trị (không hiển thị giá trị).")
        return 0

    if args.command == "activate":
        applications_path = args.state_dir / "applications.json"
        applications = json.loads(applications_path.read_text(encoding="utf-8")) if applications_path.exists() else []
        application = next((item for item in applications if item.get("id") == args.application_id), None)
        if not application:
            print("Không tìm thấy hồ sơ đăng ký.", file=sys.stderr)
            return 2
        student = portal.activate_student(
            application_id=application["id"],
            display_name=application["full_name"],
            phone=application["phone"],
            cohort=args.cohort,
        )
        print(f"Đã kích hoạt: {student['display_name']} · {student['id']} · cohort {student['cohort']}")
        return 0

    students_path = args.state_dir / "students.json"
    students = json.loads(students_path.read_text(encoding="utf-8")) if students_path.exists() else []
    for student in students:
        status = "Đang học" if student.get("active") else "Đã khóa"
        print(f"{student.get('display_name')} · {student.get('id')} · {student.get('cohort')} · {status}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
