from datetime import datetime
from typing import List, Optional


def require_non_empty(value: str, field_name: str) -> str:
    if not value or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value.strip()


def parse_date(value: str) -> Optional[datetime]:
    if not value or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.strip())
    except ValueError:
        raise ValueError(f'Invalid date: "{value}". Use YYYY-MM-DD format.')


def parse_tags(raw: str) -> List[str]:
    if not raw or not raw.strip():
        return []
    return [t.strip().lower() for t in raw.split(",") if t.strip()]
