from typing import List
from src.models import Note


class ConsoleView:
    """All console output (View in MVC)."""

    def separator(self, char: str = "─", length: int = 50) -> None:
        print(char * length)

    def header(self, text: str) -> None:
        self.separator("═")
        print(f"  {text}")
        self.separator("═")

    def menu(self, options: list) -> None:
        self.separator()
        for key, label in options:
            print(f"  [{key}] {label}")
        self.separator()

    def success(self, msg: str) -> None:
        print(f"✔  {msg}")

    def error(self, msg: str) -> None:
        print(f"✘  ОШИБКА: {msg}")

    def info(self, msg: str) -> None:
        print(f"ℹ  {msg}")

    def note_list(self, notes: List[Note]) -> None:
        if not notes:
            self.info("Заметки не найдены.")
            return
        for i, n in enumerate(notes, 1):
            print(f"  {i}. [{n.id}] {n}")

    def note_detail(self, note: Note) -> None:
        self.separator()
        print(note.display())
        self.separator()
