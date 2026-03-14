#!/usr/bin/env python3
"""
Quick script to find student "Avo" and list assignments for setting due date extensions.
Run with: python scripts/find_student_and_assignment.py
"""

import asyncio
import os
import sys

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from client import ClassavoClient
from config import config  # Use the global config instance


async def main():
    client = ClassavoClient()  # Uses global config

    # Login using client's login method
    print("Logging in...")
    try:
        await client.login(config.username, config.password)
        print(f"✓ Logged in as {config.username}")
    except Exception as e:
        print(f"✗ Login error: {e}")
        return

    # Get courses
    print("\n--- Courses ---")
    try:
        courses = await client.get("/api/v2/courses/")
        courses_list = courses.get("results", courses) if isinstance(courses, dict) else courses
        for c in courses_list:
            print(f"  {c.get('public_id')}: {c.get('name')}")

        if not courses_list:
            print("No courses found")
            return

        # Find Quiz 101 course
        course = None
        for c in courses_list:
            if "quiz" in c.get("name", "").lower():
                course = c
                break

        if not course:
            print("✗ Quiz course not found")
            return

        public_id = course.get("public_id")
        print(f"\n→ Using course: {public_id} - {course.get('name')}")
    except Exception as e:
        print(f"✗ Error getting courses: {e}")
        return

    # Get roster - find student "Avo"
    print("\n--- Looking for student 'Avo' ---")
    try:
        roster = await client.get(f"/api/courses/{public_id}/students")
        students = roster if isinstance(roster, list) else roster.get("students", [])

        avo_student = None
        for student in students:
            name = f"{student.get('first_name', '')} {student.get('last_name', '')}".strip()
            email = student.get("email", "")
            identity = student.get("identity")

            # Check if this is "Avo"
            if "avo" in name.lower() or "avo" in email.lower():
                avo_student = student
                print(f"  ✓ FOUND: {name} ({email})")
                print(f"    Student ID: {identity}")
            else:
                print(f"  - {name} ({email}) - {identity}")

        if not avo_student:
            print("\n⚠ Student 'Avo' not found in roster")
    except Exception as e:
        print(f"✗ Error getting roster: {e}")

    # Get drive root to find all items
    print("\n--- Drive Items (files, chapters, playlists) ---")
    try:
        # Get root folder
        root_info = await client.get(f"/api/courses/{public_id}/folder")
        root_id = root_info.get("identity")

        # Get folder contents
        folder = await client.get(f"/api/folder/{root_id}")
        items = folder.get("items", [])

        print(f"Found {len(items)} items in drive:")
        for item in items:
            title = item.get("title")
            item_type = item.get("file_type") or item.get("item_type")
            identity = item.get("identity")
            print(f"  [{item_type}] {identity}: {title}")

            # Try to get schedules for this item
            try:
                schedules_resp = await client.get(f"/api/v2/drive/items/{item_type}/{identity}/schedules")
                schedules = schedules_resp.get("schedules", [])
                if schedules:
                    for s in schedules:
                        scope = "ALL" if s.get("scope") == 1 else "INDIVIDUAL"
                        end_date = s.get("end_date", "No due date")
                        targets = s.get("targets", [])
                        if scope == "ALL":
                            print(f"      → Due: {end_date} (all students)")
                        else:
                            print(f"      → Due: {end_date} (individual: {len(targets)} targets)")
            except Exception:
                pass  # No schedules or error

    except Exception as e:
        print(f"✗ Error getting drive items: {e}")

    print("\n--- Done ---")
    print("\nTo set Avo's due date extension, use:")
    print("  set_student_due_date(")
    print("      item_id='<assignment-uuid-from-above>',")
    print("      item_type='assignment',")
    print("      student_id='<avo-student-uuid>',")
    print("      end_date='2025-04-20T23:59:59Z'")
    print("  )")


if __name__ == "__main__":
    asyncio.run(main())
