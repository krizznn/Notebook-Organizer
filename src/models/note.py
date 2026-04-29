from datetime import datetime
from typing import List, Optional


class Note:
    """Base note model with validation."""

    def __init__(
        self,
        title: str,
        text: str,
        tags: Optional[List[str]] = None,
        date: Optional[str] = None,
        note_id: Optional[str] = None,
        note_type: str = "text",
    ):
        if not title or not title.strip():
            raise ValueError("Title must be a non-empty string")
        if not text or not text.strip():
            raise ValueError("Text must be a non-empty string")
        if tags is not None and not isinstance(tags, list):
            raise ValueError("Tags must be a list")

        self.id = note_id or self._generate_id()
        self.title = title.strip()
        self.text = text.strip()
        self.tags = [t.strip().lower() for t in (tags or []) if t.strip()]
        self.type = note_type

        if date:
            try:
                self.date = datetime.fromisoformat(date)
            except ValueError:
                raise ValueError(f'Invalid date format: "{date}"')
        else:
            self.date = datetime.now()

    @staticmethod
    def _generate_id() -> str:
        import uuid
        return str(uuid.uuid4())[:12]

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "title": self.title,
            "text": self.text,
            "tags": self.tags,
            "date": self.date.isoformat(),
            "type": self.type,
        }

    def display(self) -> str:
        tags_str = ", ".join(self.tags) if self.tags else "—"
        return (
            f"ID:    {self.id}\n"
            f"Type:  {self.type}\n"
            f"Title: {self.title}\n"
            f"Date:  {self.date.strftime('%Y-%m-%d %H:%M')}\n"
            f"Tags:  {tags_str}\n"
            f"Text:\n  {self.text}"
        )

    def __str__(self) -> str:
        return f"[{self.type.upper()}] {self.title} ({self.date.strftime('%Y-%m-%d')})"
