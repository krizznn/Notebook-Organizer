from .text_note import TextNote
from .voice_note import VoiceNote
from .note import Note


class NoteFactory:
    """Creates the correct Note subclass based on the 'type' field."""

    @staticmethod
    def create(data: dict) -> Note:
        note_type = data.get("type", "text").lower()
        common = {
            "title": data["title"],
            "text": data["text"],
            "tags": data.get("tags", []),
            "date": data.get("date"),
            "note_id": data.get("id"),
        }
        if note_type == "voice":
            return VoiceNote(
                duration=data.get("duration", 0),
                transcription=data.get("transcription", ""),
                **common,
            )
        # default → TextNote
        return TextNote(category=data.get("category", "general"), **common)
