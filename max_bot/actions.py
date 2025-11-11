
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from llm.tags import get_tags_from_openai
from telegram_bot import db

# Read README file for the help function
with open("README.md", "r", encoding="utf-8") as f:
    README_TEXT = f.read()

async def get_help() -> str:
    """Returns the content of the README.md file."""
    return README_TEXT

async def report_issue(report_text: str) -> dict:
    """Reports an issue to the admin."""
    return {
        "action": "send_report",
        "text": report_text,
        "user_message": "Спасибо за ваш отзыв! Я передал его разработчику."
    }

async def view_notes(user_db_id: int) -> str:
    """Shows all notes."""
    user_notes = db.get_notes(user_db_id)
    if not user_notes:
        return "У вас пока нет заметок."
    else:
        message = "Ваши заметки:\n"
        for i, note in enumerate(user_notes):
            tags = ", ".join(note.get("tags", []))
            message += f"{note['id']}. {note['text']}\n   Tags: {tags}\n"
        return message

async def add_note(user_db_id: int, note_text: str) -> str:
    """Adds a note."""
    tags = await get_tags_from_openai(note_text)
    db.add_note(user_db_id, note_text, tags)
    return f"Заметка добавлена: {note_text}\nТеги: {', '.join(tags)}"

async def delete_note(note_id: int, user_db_id: int) -> str:
    """Deletes a note."""
    db.delete_note(note_id, user_db_id)
    return f"Заметка {note_id} удалена."

async def edit_note(note_id: int, new_text: str, user_db_id: int) -> str:
    """Edits a note."""
    tags = await get_tags_from_openai(new_text)
    db.edit_note(note_id, new_text, tags, user_db_id)
    return f"Заметка {note_id} отредактирована.\nНовые теги: {', '.join(tags)}"

async def find_by_tag(user_db_id: int, tag: str) -> str:
    """Finds notes by tag."""
    found_notes = db.find_notes_by_tag(user_db_id, tag)

    if not found_notes:
        return f"Заметок с тегом '{tag}' не найдено."
    else:
        message = f"Заметки с тегом '{tag}':\n"
        for i, note in enumerate(found_notes):
            message += f"{note['id']}. {note['text']}\n"
        return message
