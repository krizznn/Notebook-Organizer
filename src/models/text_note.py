from .note import Note


class TextNote(Note):
    """Text note with an optional category field."""

    def __init__(self, category: str = "general", **kwargs):
        super().__init__(**kwargs, note_type="text")
        self.category = category.strip() if category else "general"

    def to_dict(self) -> dict:
        data = super().to_dict()
        data["category"] = self.category
        return data

    def display(self) -> str:
        return super().display() + f"\nCategory: {self.category}"
