from datetime import datetime
from typing import List, Optional

from src.models import Note, NoteFactory
from src.repository import NoteRepository
from src.utils import UndoStack


class NoteService:
    """Business logic: CRUD, filtering, undo."""

    def __init__(self, repository: NoteRepository):
        self._repo = repository
        self._notes: List[Note] = []
        self._undo_stack = UndoStack(max_size=50)

    # ── Lifecycle ──────────────────────────────────────────────────────────

    def load(self) -> None:
        self._notes = self._repo.load()

    def save(self) -> None:
        self._repo.save(self._notes)

    # ── Helpers ────────────────────────────────────────────────────────────

    def _snapshot(self) -> None:
        self._undo_stack.push(self._notes)

    def _find_by_id(self, note_id: str) -> Note:
        for note in self._notes:
            if note.id == note_id:
                return note
        raise ValueError(f'Note with id "{note_id}" not found')

    # ── CRUD ───────────────────────────────────────────────────────────────

    def create(self, data: dict) -> Note:
        self._snapshot()
        note = NoteFactory.create(data)
        self._notes.append(note)
        self.save()
        return note

    def get_all(self) -> List[Note]:
        return list(self._notes)

    def get_by_id(self, note_id: str) -> Note:
        return self._find_by_id(note_id)

    def update(self, note_id: str, changes: dict) -> Note:
        self._snapshot()
        note = self._find_by_id(note_id)
        merged = {**note.to_dict(), **changes, "id": note_id}
        updated = NoteFactory.create(merged)
        idx = self._notes.index(note)
        self._notes[idx] = updated
        self.save()
        return updated

    def delete(self, note_id: str) -> Note:
        self._snapshot()
        note = self._find_by_id(note_id)
        self._notes.remove(note)
        self.save()
        return note

    # ── Filtering ──────────────────────────────────────────────────────────

    def filter_by_tag(self, tag: str) -> List[Note]:
        t = tag.strip().lower()
        return [n for n in self._notes if t in n.tags]

    def filter_by_date(
        self,
        from_date: Optional[datetime] = None,
        to_date: Optional[datetime] = None,
    ) -> List[Note]:
        result = []
        for n in self._notes:
            if from_date and n.date < from_date:
                continue
            if to_date and n.date > to_date:
                continue
            result.append(n)
        return result

    def filter_by_type(self, note_type: str) -> List[Note]:
        return [n for n in self._notes if n.type == note_type.lower()]

    def search(self, query: str) -> List[Note]:
        q = query.strip().lower()
        return [
            n for n in self._notes
            if q in n.title.lower()
            or q in n.text.lower()
            or any(q in t for t in n.tags)
        ]

    # ── Undo ───────────────────────────────────────────────────────────────

    def undo(self) -> List[Note]:
        snapshot = self._undo_stack.pop()
        if snapshot is None:
            raise RuntimeError("Nothing to undo")
        self._notes = [NoteFactory.create(d) for d in snapshot]
        self.save()
        return self._notes

    @property
    def undo_stack_size(self) -> int:
        return self._undo_stack.size
