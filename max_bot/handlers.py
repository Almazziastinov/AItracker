import logging
import os
import uuid
from maxapi import Router
from maxapi.types import MessageCreated, Filter
from llm.agent.agent import run_agent_async
from llm.transcription import transcribe_audio
from db.schema import get_db
from db.postgres import get_or_create_user

logger = logging.getLogger(__name__)
router = Router()

@router.message_created(Filter.text)
async def handle_text_message(event: MessageCreated):
    """
    Handles incoming text messages.
    """
    try:
        user_id_str = str(event.chat_id)
        message_text = event.message.text

        db_session = next(get_db())
        user = get_or_create_user(db_session, user_id_str)
        db_session.close()

        await event.bot.send_chat_action(chat_id=event.chat_id, action="typing")
        agent_response = await run_agent_async(message_text, user.id)
        await event.message.answer(agent_response)

    except Exception as e:
        logger.error(f"Error handling text message: {e}")
        await event.message.answer("Простите, произошла ошибка. Попробуйте еще раз позже.")

@router.message_created(Filter.voice)
async def handle_voice_message(event: MessageCreated):
    """
    Handles incoming voice messages.
    """
    file_path = None
    try:
        user_id_str = str(event.chat_id)
        
        # 1. Download the voice message
        # Assuming the voice object has a method to get the file content.
        # This part is speculative and depends on the maxapi library's features.
        voice = event.message.voice
        if not voice:
            await event.message.answer("Не удалось получить голосовое сообщение.")
            return

        # Create a unique filename
        file_name = f"{uuid.uuid4()}.oga"
        file_path = os.path.join("output", file_name)
        os.makedirs("output", exist_ok=True)

        # The maxapi library might not have a direct download_to_drive method.
        # I'll assume I can get the file bytes and write them to a file.
        # This is a common pattern.
        # I'll need to check the library's source if this doesn't work.
        file_content = await event.bot.download_file(voice.file_id)
        with open(file_path, "wb") as f:
            f.write(file_content)

        await event.message.answer("Расшифровываю голосовое...")
        await event.bot.send_chat_action(chat_id=event.chat_id, action="typing")

        # 2. Transcribe the audio
        transcribed_text = await transcribe_audio(file_path)

        if transcribed_text:
            # 3. Process the transcribed text with the agent
            db_session = next(get_db())
            user = get_or_create_user(db_session, user_id_str)
            db_session.close()
            
            agent_response = await run_agent_async(transcribed_text, user.id)
            await event.message.answer(agent_response)
        else:
            await event.message.answer("Не удалось расшифровать голосовое сообщение. Попробуйте еще раз.")

    except Exception as e:
        logger.error(f"Error handling voice message: {e}")
        await event.message.answer("Произошла ошибка при обработке вашего голосового сообщения.")
    finally:
        # 4. Clean up the downloaded file
        if file_path and os.path.exists(file_path):
            os.remove(file_path)