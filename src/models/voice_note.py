from .note import Note


class VoiceNote(Note):
    """Voice note with duration and transcription fields."""

    def __init__(self, duration: int = 0, transcription: str = "", **kwargs):
        super().__init__(**kwargs, note_type="voice")
        duration = int(duration)
        if duration < 0:
            raise ValueError("Duration must be a non-negative integer (seconds)")
        self.duration = duration
        self.transcription = transcription.strip() if transcription else ""

    def _format_duration(self) -> str:
        m, s = divmod(self.duration, 60)
        return f"{m}:{s:02d}"

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["duration"] = self.duration
        data["transcription"] = self.transcription
        return data

    def display(self) -> str:
        lines = [super().display(), f"Duration: {self._format_duration()}"]
        if self.transcription:
            lines.append(f"Transcription: {self.transcription}")
        return "\n".join(lines)
