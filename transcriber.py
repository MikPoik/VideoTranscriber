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

async def transcribe_audio(audio_file, language="fi",model="whisper-large"):
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
            model=model,
            smart_format=True,
            language=language,
            punctuate=True,
            paragraphs=True
        )

        response = await deepgram.listen.asyncrest.v("1").transcribe_file(
            payload, options, timeout=httpx.Timeout(300.0, connect=10.0)
        )
        duration = response["metadata"]["duration"]

        return response.to_dict(),duration

    except Exception as e:
        raise Exception(f"Error transcribing audio with Deepgram: {str(e)}")
