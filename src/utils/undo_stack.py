from typing import List, Optional


class UndoStack:
    """
    LIFO stack that stores snapshots (dicts) of the notes list
    before each mutating operation, enabling undo.
    """

    def __init__(self, max_size: int = 50):
        self._stack: List[list] = []
        self._max_size = max_size

    def push(self, notes: list) -> None:
        """Push a deep snapshot of the current notes list."""
        snapshot = [n.to_dict() for n in notes]
        self._stack.append(snapshot)
        if len(self._stack) > self._max_size:
            self._stack.pop(0)  # evict oldest

    def pop(self) -> Optional[list]:
        """Return the last snapshot or None if empty."""
        return self._stack.pop() if self._stack else None

    def is_empty(self) -> bool:
        return len(self._stack) == 0

    def clear(self) -> None:
        self._stack.clear()

    @property
    def size(self) -> int:
        return len(self._stack)
