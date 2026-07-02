"""Application versioning and update settings."""

APP_NAME = "Time Clock System"
APP_VERSION = "1.1.0"

# Set this to your GitHub repository in the format "owner/repo".
# Example: GITHUB_REPO = "judsonfitzpatrick/time-clock"
GITHUB_REPO = ""


def parse_version(version: str):
    """Convert semantic-ish version text into a comparable tuple of integers."""
    cleaned = (version or "").strip().lstrip("vV")
    parts = []
    for token in cleaned.split("."):
        digits = ""
        for ch in token:
            if ch.isdigit():
                digits += ch
            else:
                break
        parts.append(int(digits) if digits else 0)

    while len(parts) < 3:
        parts.append(0)

    return tuple(parts[:3])


def is_newer_version(latest: str, current: str = APP_VERSION) -> bool:
    """Return True when the latest version is newer than current."""
    return parse_version(latest) > parse_version(current)
