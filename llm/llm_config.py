import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from max_bot import config

# GigaChat Credentials
GIGACHAT_CREDENTIALS = config.GIGACHAT_CREDENTIALS

# LLM settings
# TODO: Verify the correct model name for GigaChat
MODEL_NAME = "GigaChat-Pro" 
