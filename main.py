"""
Notebook Organizer — entry point.
Run: python main.py
"""
import sys
import os

# Allow running from project root
sys.path.insert(0, os.path.dirname(__file__))

from src.repository import NoteRepository
from src.service import NoteService
from src.view import ConsoleView
from src.controller import NoteController


def main():
    repo       = NoteRepository(file_path="data/notes.json")
    service    = NoteService(repo)
    view       = ConsoleView()
    controller = NoteController(service, view)
    controller.run()


if __name__ == "__main__":
    main()
