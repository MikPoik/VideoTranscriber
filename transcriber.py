import os
import asyncio
import aiofiles
import httpx
from datetime import datetime
from deepgram import (
    DeepgramClient,
    PrerecordedOptions,
)

DEEPGRAM_API_KEY = os.environ.get("DG_API_KEY")

async def transcribe_audio(audio_file, language="fi"):
    try:
        if not DEEPGRAM_API_KEY:
            raise ValueError("Deepgram API key is not set. Please set the DG_API_KEY environment variable.")

        deepgram = DeepgramClient(DEEPGRAM_API_KEY)
        
        async with aiofiles.open(audio_file, "rb") as file:
            buffer_data = await file.read()

        payload = {
            "buffer": buffer_data,
        }

        options = PrerecordedOptions(
            model="whisper-large",
            smart_format=True,
            language=language,
            punctuate=True,
        )

        response = await deepgram.listen.asyncrest.v("1").transcribe_file(
            payload, options, timeout=httpx.Timeout(300.0, connect=10.0)
        )

        return response.to_dict()

    except Exception as e:
        raise Exception(f"Error transcribing audio with Deepgram: {str(e)}")
