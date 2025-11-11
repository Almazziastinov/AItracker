import logging
import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from salute_speech.speech_recognition import SaluteSpeechClient
from max_bot import config

logger = logging.getLogger(__name__)

# TODO: Verify if GIGACHAT_CREDENTIALS are the same as SBER_SPEECH_API_KEY.
# If not, a new environment variable for the speech API key will be needed.
client = SaluteSpeechClient(client_credentials=config.GIGACHAT_CREDENTIALS)

async def transcribe_audio(file_path: str) -> str | None:
    """
    Transcribes an audio file using the SaluteSpeech API.

    Args:
        file_path: The path to the audio file.

    Returns:
        The transcribed text, or None if an error occurs.
    """
    try:
        with open(file_path, "rb") as audio_file:
            result = await client.audio.transcriptions.create(
                file=audio_file,
                language="ru-RU" 
            )
        return result.text
    except Exception as e:
        logger.error(f"Error transcribing audio: {e}")
        return None