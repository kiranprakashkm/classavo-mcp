"""Timezone utilities for Classavo MCP Server.

Handles timezone detection and date/time conversion.
"""

import os
from datetime import datetime, timezone
from typing import Optional

# Try to import zoneinfo (Python 3.9+) or pytz as fallback
try:
    from zoneinfo import ZoneInfo
except ImportError:
    from pytz import timezone as ZoneInfo


def get_user_timezone() -> str:
    """
    Get the user's timezone from environment or system.

    Checks in order:
    1. CLASSAVO_TIMEZONE env var
    2. TZ env var
    3. System timezone
    4. Falls back to UTC

    Returns:
        Timezone string (e.g., 'America/New_York', 'Asia/Kolkata')
    """
    # Check environment variables
    tz = os.environ.get("CLASSAVO_TIMEZONE") or os.environ.get("TZ")
    if tz:
        return tz

    # Try to detect system timezone
    try:
        # macOS/Linux: read from /etc/localtime symlink
        import subprocess
        result = subprocess.run(
            ["readlink", "/etc/localtime"],
            capture_output=True,
            text=True,
            timeout=2,
        )
        if result.returncode == 0:
            # Extract timezone from path like /var/db/timezone/zoneinfo/America/Los_Angeles
            path = result.stdout.strip()
            if "zoneinfo/" in path:
                return path.split("zoneinfo/")[-1]
    except Exception:
        pass

    # Default to UTC
    return "UTC"


def utc_to_local(utc_dt_str: str, tz_name: Optional[str] = None) -> str:
    """
    Convert UTC datetime string to local timezone.

    Args:
        utc_dt_str: ISO format datetime string (e.g., "2024-03-15T23:59:59Z")
        tz_name: Target timezone (defaults to user's timezone)

    Returns:
        Formatted datetime string in local time
    """
    if not utc_dt_str:
        return None

    tz_name = tz_name or get_user_timezone()

    try:
        # Parse the UTC datetime
        if utc_dt_str.endswith("Z"):
            utc_dt_str = utc_dt_str[:-1] + "+00:00"

        utc_dt = datetime.fromisoformat(utc_dt_str.replace("Z", "+00:00"))

        # Ensure it's UTC aware
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=timezone.utc)

        # Convert to local timezone
        local_tz = ZoneInfo(tz_name)
        local_dt = utc_dt.astimezone(local_tz)

        # Format nicely
        return local_dt.strftime("%B %d, %Y at %I:%M %p %Z")
    except Exception as e:
        # Return original if conversion fails
        return utc_dt_str


def local_to_utc(local_dt_str: str, tz_name: Optional[str] = None) -> str:
    """
    Convert local datetime string to UTC ISO format.

    Args:
        local_dt_str: Datetime string (various formats supported)
        tz_name: Source timezone (defaults to user's timezone)

    Returns:
        ISO format UTC datetime string
    """
    tz_name = tz_name or get_user_timezone()

    try:
        local_tz = ZoneInfo(tz_name)

        # Try parsing various formats
        formats = [
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%dT%H:%M:%S",
            "%Y-%m-%dT%H:%M",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y %H:%M",
            "%B %d, %Y %I:%M %p",
            "%B %d, %Y at %I:%M %p",
        ]

        local_dt = None
        for fmt in formats:
            try:
                local_dt = datetime.strptime(local_dt_str, fmt)
                break
            except ValueError:
                continue

        if local_dt is None:
            # Try ISO format as fallback
            local_dt = datetime.fromisoformat(local_dt_str)

        # Add timezone if naive
        if local_dt.tzinfo is None:
            local_dt = local_dt.replace(tzinfo=local_tz)

        # Convert to UTC
        utc_dt = local_dt.astimezone(timezone.utc)

        return utc_dt.strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception as e:
        # Return original if conversion fails
        return local_dt_str


def format_due_date(utc_dt_str: str, tz_name: Optional[str] = None) -> dict:
    """
    Format a due date with both UTC and local representations.

    Args:
        utc_dt_str: ISO format UTC datetime string
        tz_name: Target timezone (defaults to user's timezone)

    Returns:
        Dict with utc, local, and relative time info
    """
    if not utc_dt_str:
        return {"utc": None, "local": None, "relative": "No due date"}

    tz_name = tz_name or get_user_timezone()
    local_str = utc_to_local(utc_dt_str, tz_name)

    # Calculate relative time
    try:
        if utc_dt_str.endswith("Z"):
            utc_dt_str_parsed = utc_dt_str[:-1] + "+00:00"
        else:
            utc_dt_str_parsed = utc_dt_str

        utc_dt = datetime.fromisoformat(utc_dt_str_parsed.replace("Z", "+00:00"))
        if utc_dt.tzinfo is None:
            utc_dt = utc_dt.replace(tzinfo=timezone.utc)

        now = datetime.now(timezone.utc)
        diff = utc_dt - now

        if diff.total_seconds() < 0:
            relative = "Past due"
        elif diff.days > 7:
            relative = f"Due in {diff.days} days"
        elif diff.days > 1:
            relative = f"Due in {diff.days} days"
        elif diff.days == 1:
            relative = "Due tomorrow"
        elif diff.seconds > 3600:
            hours = diff.seconds // 3600
            relative = f"Due in {hours} hours"
        else:
            minutes = diff.seconds // 60
            relative = f"Due in {minutes} minutes"
    except Exception:
        relative = ""

    return {
        "utc": utc_dt_str,
        "local": local_str,
        "timezone": tz_name,
        "relative": relative,
    }
