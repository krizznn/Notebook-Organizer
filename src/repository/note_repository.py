import json
import os
from typing import List

from src.models import Note, NoteFactory


class NoteRepository:
    """Handles reading and writing notes to a JSON file."""

    def __init__(self, file_path: str = "data/notes.json"):
        self._file_path = file_path
        self._ensure_file()

    def _ensure_file(self) -> None:
        os.makedirs(os.path.dirname(self._file_path), exist_ok=True)
        if not os.path.exists(self._file_path):
            with open(self._file_path, "w", encoding="utf-8") as f:
                json.dump([], f)

    def load(self) -> List[Note]:
        try:
            with open(self._file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if not isinstance(data, list):
                raise ValueError("JSON root must be an array")
            return [NoteFactory.create(item) for item in data]
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            raise RuntimeError(f"Failed to load notes: {e}")

    def save(self, notes: List[Note]) -> None:
        try:
            with open(self._file_path, "w", encoding="utf-8") as f:
                json.dump([n.to_dict() for n in notes], f, ensure_ascii=False, indent=2)
        except OSError as e:
            raise RuntimeError(f"Failed to save notes: {e}")
