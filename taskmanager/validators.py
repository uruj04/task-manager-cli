"""Input validation helpers. Each returns the cleaned value or raises ValidationError."""

from datetime import datetime

from .exceptions import ValidationError
from .models import PRIORITIES, STATUSES

MAX_TITLE_LENGTH = 80
MAX_DESCRIPTION_LENGTH = 300


def validate_title(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValidationError("Title cannot be empty.")
    if len(value) > MAX_TITLE_LENGTH:
        raise ValidationError(f"Title must be at most {MAX_TITLE_LENGTH} characters.")
    return value


def validate_description(value: str) -> str:
    value = value.strip()
    if len(value) > MAX_DESCRIPTION_LENGTH:
        raise ValidationError(
            f"Description must be at most {MAX_DESCRIPTION_LENGTH} characters."
        )
    return value


def _validate_choice(value: str, choices: tuple[str, ...], field: str) -> str:
    value = value.strip().lower()
    if value not in choices:
        raise ValidationError(f"{field} must be one of: {', '.join(choices)}.")
    return value


def validate_priority(value: str) -> str:
    return _validate_choice(value, PRIORITIES, "Priority")


def validate_status(value: str) -> str:
    return _validate_choice(value, STATUSES, "Status")


def validate_due_date(value: str) -> str:
    """Due date is optional. If given, it must be a real date as YYYY-MM-DD."""
    value = value.strip()
    if not value:
        return ""
    try:
        datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        raise ValidationError(
            "Due date must be a valid date in YYYY-MM-DD format (e.g. 2026-10-05)."
        ) from None
    return value


def validate_keyword(value: str) -> str:
    value = value.strip()
    if not value:
        raise ValidationError("Search keyword cannot be empty.")
    return value
