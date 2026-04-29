"""
Notebook Organizer — test suite.
Run: python -m pytest tests/ -v
  or: python tests/test_all.py
Covers: positive, negative, and edge/boundary cases.
"""
import sys
import os
import json
import tempfile
import unittest
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.models import Note, TextNote, VoiceNote, NoteFactory
from src.utils import UndoStack, parse_tags, parse_date, require_non_empty
from src.repository import NoteRepository
from src.service import NoteService


# ── helpers ───────────────────────────────────────────────────────────────

def make_repo():
    tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False)
    tmp.close()
    os.unlink(tmp.name)          # let NoteRepository create it fresh
    return NoteRepository(file_path=tmp.name)

def make_service():
    svc = NoteService(make_repo())
    svc.load()
    return svc


# ═══════════════════════════════════════════════════════════════════════════
#  1. Note model
# ═══════════════════════════════════════════════════════════════════════════

class TestNotePositive(unittest.TestCase):

    def test_creates_with_all_fields(self):
        n = Note(title="Hello", text="World", tags=["a", "b"])
        self.assertEqual(n.title, "Hello")
        self.assertEqual(n.text, "World")
        self.assertEqual(len(n.tags), 2)

    def test_trims_title_and_text(self):
        n = Note(title="  Hi  ", text="  Body  ")
        self.assertEqual(n.title, "Hi")
        self.assertEqual(n.text, "Body")

    def test_tags_lowercased_and_trimmed(self):
        n = Note(title="T", text="X", tags=["  Work ", "HOME"])
        self.assertIn("work", n.tags)
        self.assertIn("home", n.tags)

    def test_auto_generates_id(self):
        n = Note(title="A", text="B")
        self.assertTrue(n.id)

    def test_to_dict_round_trip(self):
        n = Note(title="A", text="B", tags=["x"])
        d = n.to_dict()
        self.assertEqual(d["title"], "A")
        self.assertIsInstance(d["date"], str)

    def test_empty_tags_allowed(self):
        n = Note(title="T", text="X", tags=[])
        self.assertEqual(len(n.tags), 0)

    def test_str_contains_title(self):
        n = Note(title="MyTitle", text="X")
        self.assertIn("MyTitle", str(n))


class TestNoteNegative(unittest.TestCase):

    def test_empty_title_raises(self):
        with self.assertRaises(ValueError):
            Note(title="", text="ok")

    def test_whitespace_title_raises(self):
        with self.assertRaises(ValueError):
            Note(title="   ", text="ok")

    def test_empty_text_raises(self):
        with self.assertRaises(ValueError):
            Note(title="T", text="")

    def test_tags_not_list_raises(self):
        with self.assertRaises(ValueError):
            Note(title="T", text="X", tags="notalist")

    def test_invalid_date_raises(self):
        with self.assertRaises(ValueError):
            Note(title="T", text="X", date="not-a-date")


# ═══════════════════════════════════════════════════════════════════════════
#  2. TextNote
# ═══════════════════════════════════════════════════════════════════════════

class TestTextNote(unittest.TestCase):

    def test_type_is_text(self):
        n = TextNote(title="T", text="X")
        self.assertEqual(n.type, "text")

    def test_default_category(self):
        n = TextNote(title="T", text="X")
        self.assertEqual(n.category, "general")

    def test_custom_category(self):
        n = TextNote(title="T", text="X", category="work")
        self.assertEqual(n.category, "work")

    def test_display_includes_category(self):
        n = TextNote(title="T", text="X", category="ideas")
        self.assertIn("Category", n.display())

    def test_to_dict_has_category(self):
        n = TextNote(title="T", text="X", category="dev")
        self.assertEqual(n.to_dict()["category"], "dev")


# ═══════════════════════════════════════════════════════════════════════════
#  3. VoiceNote
# ═══════════════════════════════════════════════════════════════════════════

class TestVoiceNote(unittest.TestCase):

    def test_type_is_voice(self):
        n = VoiceNote(title="T", text="X")
        self.assertEqual(n.type, "voice")

    def test_stores_duration(self):
        n = VoiceNote(title="T", text="X", duration=90)
        self.assertEqual(n.duration, 90)

    def test_formats_duration_mmss(self):
        n = VoiceNote(title="T", text="X", duration=75)
        self.assertIn("1:15", n.display())

    def test_negative_duration_raises(self):
        with self.assertRaises(ValueError):
            VoiceNote(title="T", text="X", duration=-1)

    def test_zero_duration_ok(self):
        n = VoiceNote(title="T", text="X", duration=0)
        self.assertEqual(n.duration, 0)

    def test_transcription_in_display(self):
        n = VoiceNote(title="T", text="X", transcription="hello world")
        self.assertIn("Transcription", n.display())

    def test_to_dict_has_duration(self):
        n = VoiceNote(title="T", text="X", duration=30)
        self.assertEqual(n.to_dict()["duration"], 30)


# ═══════════════════════════════════════════════════════════════════════════
#  4. NoteFactory
# ═══════════════════════════════════════════════════════════════════════════

class TestNoteFactory(unittest.TestCase):

    def test_creates_text_note_by_default(self):
        n = NoteFactory.create({"title": "T", "text": "X"})
        self.assertIsInstance(n, TextNote)

    def test_creates_text_note_explicitly(self):
        n = NoteFactory.create({"title": "T", "text": "X", "type": "text"})
        self.assertIsInstance(n, TextNote)

    def test_creates_voice_note(self):
        n = NoteFactory.create({"title": "T", "text": "X", "type": "voice"})
        self.assertIsInstance(n, VoiceNote)

    def test_unknown_type_falls_back_to_text(self):
        n = NoteFactory.create({"title": "T", "text": "X", "type": "unknown"})
        self.assertIsInstance(n, TextNote)


# ═══════════════════════════════════════════════════════════════════════════
#  5. UndoStack
# ═══════════════════════════════════════════════════════════════════════════

class TestUndoStack(unittest.TestCase):

    def _note(self):
        return TextNote(title="T", text="X")

    def test_starts_empty(self):
        self.assertTrue(UndoStack().is_empty())

    def test_push_pop_round_trip(self):
        s = UndoStack()
        s.push([self._note()])
        snap = s.pop()
        self.assertIsInstance(snap, list)
        self.assertEqual(len(snap), 1)
        self.assertEqual(snap[0]["title"], "T")

    def test_pop_returns_none_when_empty(self):
        self.assertIsNone(UndoStack().pop())

    def test_respects_max_size(self):
        s = UndoStack(max_size=3)
        n = self._note()
        for _ in range(5):
            s.push([n])
        self.assertEqual(s.size, 3)

    def test_size_grows_with_push(self):
        s = UndoStack()
        n = self._note()
        s.push([n]); s.push([n])
        self.assertEqual(s.size, 2)

    def test_clear_resets(self):
        s = UndoStack()
        s.push([self._note()])
        s.clear()
        self.assertTrue(s.is_empty())


# ═══════════════════════════════════════════════════════════════════════════
#  6. Validator
# ═══════════════════════════════════════════════════════════════════════════

class TestValidator(unittest.TestCase):

    def test_parse_tags_splits_by_comma(self):
        t = parse_tags("a, B, c")
        self.assertEqual(sorted(t), ["a", "b", "c"])

    def test_parse_tags_empty_string(self):
        self.assertEqual(parse_tags(""), [])

    def test_parse_tags_none(self):
        self.assertEqual(parse_tags(None), [])

    def test_parse_tags_filters_empty_segments(self):
        t = parse_tags(",, ,a,,")
        self.assertEqual(t, ["a"])

    def test_parse_date_valid(self):
        d = parse_date("2024-01-15")
        self.assertIsInstance(d, datetime)

    def test_parse_date_invalid_raises(self):
        with self.assertRaises(ValueError):
            parse_date("not-a-date")

    def test_parse_date_none_returns_none(self):
        self.assertIsNone(parse_date(None))
        self.assertIsNone(parse_date(""))

    def test_require_non_empty_trims(self):
        self.assertEqual(require_non_empty("  hi  ", "f"), "hi")

    def test_require_non_empty_raises_for_blank(self):
        with self.assertRaises(ValueError):
            require_non_empty("  ", "FieldX")


# ═══════════════════════════════════════════════════════════════════════════
#  7. NoteRepository
# ═══════════════════════════════════════════════════════════════════════════

class TestNoteRepository(unittest.TestCase):

    def test_creates_file_and_loads_empty(self):
        repo = make_repo()
        self.assertEqual(repo.load(), [])

    def test_save_and_load_text_note(self):
        repo = make_repo()
        n = TextNote(title="Persist", text="test", tags=["x"])
        repo.save([n])
        loaded = repo.load()
        self.assertEqual(len(loaded), 1)
        self.assertEqual(loaded[0].title, "Persist")
        self.assertIsInstance(loaded[0], TextNote)

    def test_save_and_load_voice_note(self):
        repo = make_repo()
        n = VoiceNote(title="V", text="desc", duration=42)
        repo.save([n])
        loaded = repo.load()
        self.assertIsInstance(loaded[0], VoiceNote)
        self.assertEqual(loaded[0].duration, 42)

    def test_malformed_json_raises(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
        tmp.write("{not valid json}")
        tmp.close()
        repo = NoteRepository(file_path=tmp.name)
        with self.assertRaises(RuntimeError):
            repo.load()

    def test_json_object_root_raises(self):
        tmp = tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w")
        json.dump({"key": "val"}, tmp)
        tmp.close()
        repo = NoteRepository(file_path=tmp.name)
        with self.assertRaises(RuntimeError):
            repo.load()


# ═══════════════════════════════════════════════════════════════════════════
#  8. NoteService — CRUD
# ═══════════════════════════════════════════════════════════════════════════

class TestNoteServiceCRUD(unittest.TestCase):

    def test_create_returns_note(self):
        svc = make_service()
        n = svc.create({"title": "T", "text": "X"})
        self.assertTrue(n.id)

    def test_get_all_returns_all(self):
        svc = make_service()
        svc.create({"title": "A", "text": "X"})
        svc.create({"title": "B", "text": "Y"})
        self.assertEqual(len(svc.get_all()), 2)

    def test_get_by_id_finds_note(self):
        svc = make_service()
        n = svc.create({"title": "Find me", "text": "X"})
        self.assertEqual(svc.get_by_id(n.id).title, "Find me")

    def test_get_by_id_raises_for_unknown(self):
        svc = make_service()
        with self.assertRaises(ValueError):
            svc.get_by_id("NOPE")

    def test_update_changes_title(self):
        svc = make_service()
        n = svc.create({"title": "Old", "text": "X"})
        up = svc.update(n.id, {"title": "New"})
        self.assertEqual(up.title, "New")

    def test_update_raises_for_unknown(self):
        svc = make_service()
        with self.assertRaises(ValueError):
            svc.update("NOPE", {"title": "X"})

    def test_delete_removes_note(self):
        svc = make_service()
        n = svc.create({"title": "Bye", "text": "X"})
        svc.delete(n.id)
        self.assertEqual(len(svc.get_all()), 0)

    def test_delete_raises_for_unknown(self):
        svc = make_service()
        with self.assertRaises(ValueError):
            svc.delete("NOPE")


# ═══════════════════════════════════════════════════════════════════════════
#  9. NoteService — filtering
# ═══════════════════════════════════════════════════════════════════════════

class TestNoteServiceFiltering(unittest.TestCase):

    def _populated(self):
        svc = make_service()
        svc.create({"title": "Work task", "text": "Do it", "tags": ["work", "urgent"]})
        svc.create({"title": "Shopping",  "text": "Buy food", "tags": ["personal"]})
        svc.create({"title": "Voice memo", "text": "Remember", "tags": ["work"],
                    "type": "voice", "duration": 30})
        return svc

    def test_filter_by_tag_returns_matching(self):
        self.assertEqual(len(self._populated().filter_by_tag("work")), 2)

    def test_filter_by_tag_case_insensitive(self):
        self.assertEqual(len(self._populated().filter_by_tag("WORK")), 2)

    def test_filter_by_tag_unknown(self):
        self.assertEqual(len(self._populated().filter_by_tag("nope")), 0)

    def test_filter_by_type_voice(self):
        self.assertEqual(len(self._populated().filter_by_type("voice")), 1)

    def test_filter_by_date_wide_range(self):
        svc = self._populated()
        result = svc.filter_by_date(datetime(2000, 1, 1), datetime(2099, 12, 31))
        self.assertEqual(len(result), 3)

    def test_filter_by_date_future_from(self):
        svc = self._populated()
        result = svc.filter_by_date(from_date=datetime(2099, 1, 1))
        self.assertEqual(len(result), 0)

    def test_search_by_title(self):
        self.assertEqual(len(self._populated().search("shop")), 1)

    def test_search_by_tag(self):
        self.assertEqual(len(self._populated().search("urgent")), 1)

    def test_search_no_match(self):
        self.assertEqual(len(self._populated().search("zzznomatch")), 0)

    def test_search_empty_returns_all(self):
        self.assertEqual(len(self._populated().search("")), 3)


# ═══════════════════════════════════════════════════════════════════════════
#  10. NoteService — undo
# ═══════════════════════════════════════════════════════════════════════════

class TestNoteServiceUndo(unittest.TestCase):

    def test_undo_after_create(self):
        svc = make_service()
        svc.create({"title": "Temp", "text": "X"})
        svc.undo()
        self.assertEqual(len(svc.get_all()), 0)

    def test_undo_after_delete_restores(self):
        svc = make_service()
        n = svc.create({"title": "Keep", "text": "X"})
        svc.delete(n.id)
        svc.undo()
        self.assertEqual(len(svc.get_all()), 1)

    def test_undo_after_update_reverts(self):
        svc = make_service()
        n = svc.create({"title": "Original", "text": "X"})
        svc.update(n.id, {"title": "Changed"})
        svc.undo()
        self.assertEqual(svc.get_by_id(n.id).title, "Original")

    def test_multiple_undos(self):
        svc = make_service()
        svc.create({"title": "A", "text": "X"})
        svc.create({"title": "B", "text": "Y"})
        svc.undo()
        self.assertEqual(len(svc.get_all()), 1)
        svc.undo()
        self.assertEqual(len(svc.get_all()), 0)

    def test_undo_empty_stack_raises(self):
        svc = make_service()
        with self.assertRaises(RuntimeError):
            svc.undo()


# ═══════════════════════════════════════════════════════════════════════════
#  11. Edge / boundary cases
# ═══════════════════════════════════════════════════════════════════════════

class TestEdgeCases(unittest.TestCase):

    def test_single_char_title(self):
        n = Note(title="A", text="X")
        self.assertEqual(n.title, "A")

    def test_100_tags(self):
        tags = [f"tag{i}" for i in range(100)]
        n = Note(title="Big", text="X", tags=tags)
        self.assertEqual(len(n.tags), 100)

    def test_two_notes_same_title_have_different_ids(self):
        svc = make_service()
        a = svc.create({"title": "Dup", "text": "X"})
        b = svc.create({"title": "Dup", "text": "Y"})
        self.assertNotEqual(a.id, b.id)

    def test_get_all_returns_copy(self):
        svc = make_service()
        svc.create({"title": "T", "text": "X"})
        all_notes = svc.get_all()
        all_notes.clear()
        self.assertEqual(len(svc.get_all()), 1)

    def test_voice_note_zero_duration(self):
        n = VoiceNote(title="T", text="X", duration=0)
        self.assertEqual(n.duration, 0)

    def test_unicode_title_and_text(self):
        n = Note(title="Заметка", text="Текст на русском")
        self.assertEqual(n.title, "Заметка")

    def test_persistence_survives_reload(self):
        repo = make_repo()
        svc1 = NoteService(repo)
        svc1.load()
        svc1.create({"title": "Saved", "text": "X"})

        svc2 = NoteService(repo)
        svc2.load()
        self.assertEqual(svc2.get_all()[0].title, "Saved")


# ═══════════════════════════════════════════════════════════════════════════

if __name__ == "__main__":
    unittest.main(verbosity=2)
