#!/usr/bin/env python3
"""
Test script to set individual due date for student Avo.
"""

import asyncio
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv
load_dotenv()

from client import ClassavoClient
from config import config


async def main():
    client = ClassavoClient()

    # Login
    print("Logging in...")
    await client.login(config.username, config.password)
    print("✓ Logged in")

    # Test data
    item_id = "d1b7b918-4a62-496b-b50a-4563afbe3f0e"  # Archive folder
    item_type = "folder"
    student_id = "8a9c9500-62ad-4dca-9b18-67b5454edb71"  # Avo
    new_due_date = "2025-04-20T23:59:59Z"  # April 20th extension

    # Step 1: Get current schedules
    print(f"\n--- Current Schedules for {item_type} {item_id} ---")
    current = await client.get(f"/api/v2/drive/items/{item_type}/{item_id}/schedules")
    current_schedules = current.get("schedules", [])

    for s in current_schedules:
        scope = "ALL" if s.get("scope") == 1 else "INDIVIDUAL"
        print(f"  Scope: {scope}, Due: {s.get('end_date')}, Targets: {s.get('targets', [])}")

    # Step 2: Build new schedules - keep class schedule, add student extension
    new_schedules = []

    # Keep class-wide schedule
    for s in current_schedules:
        if s.get("scope") == 1:
            new_schedules.append({
                "scope": 1,
                "targets": [],
                "start_date": s.get("start_date"),
                "end_date": s.get("end_date"),
            })

    # Add individual schedule for Avo
    new_schedules.append({
        "scope": 2,  # INCLUDE - specific targets
        "targets": [
            {
                "target": 1,  # STUDENT
                "target_id": student_id,
            }
        ],
        "end_date": new_due_date,
    })

    print(f"\n--- Setting individual due date for Avo ---")
    print(f"  New due date: {new_due_date}")

    # Step 3: Apply the schedules
    result = await client.post(
        f"/api/v2/drive/items/{item_id}/assign-v3",
        data={
            "item_type": item_type,
            "include_subfolders": False,
            "schedules": new_schedules,
        },
    )

    print(f"✓ Result: {result}")

    # Step 4: Verify - get updated schedules
    print(f"\n--- Updated Schedules ---")
    updated = await client.get(f"/api/v2/drive/items/{item_type}/{item_id}/schedules")
    updated_schedules = updated.get("schedules", [])

    for s in updated_schedules:
        scope = "ALL" if s.get("scope") == 1 else "INDIVIDUAL"
        targets = s.get("target_info", s.get("targets", []))
        print(f"  Scope: {scope}, Due: {s.get('end_date')}")
        if scope == "INDIVIDUAL":
            for t in targets:
                name = t.get("name") or t.get("email") or t.get("target_id")
                print(f"    → Student: {name}")

    print("\n✓ Done! Avo now has a separate due date of April 20th, 2025")


if __name__ == "__main__":
    asyncio.run(main())
