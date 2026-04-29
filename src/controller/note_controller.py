from src.service import NoteService
from src.view import ConsoleView
from src.utils import parse_tags, parse_date


class NoteController:
    """Handles user input and delegates to NoteService (MVC Controller)."""

    def __init__(self, service: NoteService, view: ConsoleView):
        self._service = service
        self._view = view

    # ── Helpers ────────────────────────────────────────────────────────────

    def _ask(self, question: str) -> str:
        return input(f"  {question}: ").strip()

    # ── Main loop ──────────────────────────────────────────────────────────

    def run(self) -> None:
        self._service.load()
        self._view.header("📓  Notebook Organizer")

        menu = [
            ("1", "Список всех заметок"),
            ("2", "Добавить TextNote"),
            ("3", "Добавить VoiceNote"),
            ("4", "Просмотреть заметку"),
            ("5", "Изменить заметку"),
            ("6", "Удалить заметку"),
            ("7", "Фильтр по тегу"),
            ("8", "Фильтр по дате"),
            ("9", "Поиск"),
            ("U", "Отменить действие (Undo)"),
            ("Q", "Выход"),
        ]

        while True:
            self._view.menu(menu)
            choice = self._ask("Выберите пункт").upper()

            try:
                if choice == "1":
                    self._list_all()
                elif choice == "2":
                    self._add_text()
                elif choice == "3":
                    self._add_voice()
                elif choice == "4":
                    self._view_note()
                elif choice == "5":
                    self._update_note()
                elif choice == "6":
                    self._delete_note()
                elif choice == "7":
                    self._filter_by_tag()
                elif choice == "8":
                    self._filter_by_date()
                elif choice == "9":
                    self._search()
                elif choice == "U":
                    self._undo()
                elif choice == "Q":
                    break
                else:
                    self._view.error("Неизвестный пункт меню.")
            except (ValueError, RuntimeError) as e:
                self._view.error(str(e))

        self._view.success("До свидания!")

    # ── Actions ────────────────────────────────────────────────────────────

    def _list_all(self) -> None:
        notes = self._service.get_all()
        self._view.info(f"Всего заметок: {len(notes)}")
        self._view.note_list(notes)

    def _add_text(self) -> None:
        title    = self._ask("Заголовок")
        text     = self._ask("Текст")
        tags_raw = self._ask("Теги (через запятую, необязательно)")
        category = self._ask("Категория (необязательно, по умолчанию: general)")

        note = self._service.create({
            "title": title,
            "text": text,
            "tags": parse_tags(tags_raw),
            "category": category or "general",
            "type": "text",
        })
        self._view.success(f"TextNote создана: {note.id}")

    def _add_voice(self) -> None:
        title         = self._ask("Заголовок")
        text          = self._ask("Описание")
        tags_raw      = self._ask("Теги (через запятую, необязательно)")
        duration_str  = self._ask("Длительность в секундах (необязательно, по умолчанию 0)")
        transcription = self._ask("Транскрипция (необязательно)")

        note = self._service.create({
            "title": title,
            "text": text,
            "tags": parse_tags(tags_raw),
            "duration": int(duration_str) if duration_str else 0,
            "transcription": transcription,
            "type": "voice",
        })
        self._view.success(f"VoiceNote создана: {note.id}")

    def _view_note(self) -> None:
        self._list_all()
        note_id = self._ask("Введите ID заметки")
        note = self._service.get_by_id(note_id)
        self._view.note_detail(note)

    def _update_note(self) -> None:
        self._list_all()
        note_id  = self._ask("Введите ID заметки для изменения")
        existing = self._service.get_by_id(note_id)

        self._view.info("Нажмите Enter, чтобы оставить текущее значение.")
        title    = self._ask(f"Заголовок [{existing.title}]")
        text     = self._ask(f"Текст [{existing.text[:30]}…]")
        tags_raw = self._ask(f"Теги [{', '.join(existing.tags)}]")

        changes = {}
        if title:    changes["title"] = title
        if text:     changes["text"]  = text
        if tags_raw: changes["tags"]  = parse_tags(tags_raw)

        updated = self._service.update(note_id, changes)
        self._view.success(f"Заметка обновлена: {updated.id}")

    def _delete_note(self) -> None:
        self._list_all()
        note_id = self._ask("Введите ID заметки для удаления")
        deleted = self._service.delete(note_id)
        self._view.success(f"Удалено: {deleted.title}")

    def _filter_by_tag(self) -> None:
        tag     = self._ask("Тег для фильтрации")
        results = self._service.filter_by_tag(tag)
        self._view.info(f'Заметки с тегом "{tag}":')
        self._view.note_list(results)

    def _filter_by_date(self) -> None:
        from_str = self._ask("С даты (ГГГГ-ММ-ДД, необязательно)")
        to_str   = self._ask("По дату (ГГГГ-ММ-ДД, необязательно)")
        from_dt  = parse_date(from_str)
        to_dt    = parse_date(to_str)

        results = self._service.filter_by_date(from_dt, to_dt)
        self._view.info(f"Найдено заметок: {len(results)}")
        self._view.note_list(results)

    def _search(self) -> None:
        query   = self._ask("Поисковый запрос")
        results = self._service.search(query)
        self._view.info(f'Результаты для "{query}": {len(results)}')
        self._view.note_list(results)

    def _undo(self) -> None:
        notes = self._service.undo()
        self._view.success(f"Отменено. Заметок восстановлено: {len(notes)}")
