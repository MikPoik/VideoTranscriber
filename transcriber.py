import os
from deepgram import Deepgram
from deepgram.clients.prerecorded import PrerecordedOptions

DEEPGRAM_API_KEY = os.environ.get("DG_API_KEY")

async def transcribe_audio(audio_file, language="fi"):
    try:
        if not DEEPGRAM_API_KEY:
            raise ValueError("Deepgram API key is not set. Please set the DG_API_KEY environment variable.")

        deepgram = Deepgram(DEEPGRAM_API_KEY)
        options = PrerecordedOptions(
            model="nova-2",
            smart_format=True,
            language=language,
            punctuate=True,
        )

        with open(audio_file, "rb") as audio:
            source = {"buffer": audio, "mimetype": "audio/wav"}
            response = await deepgram.transcription.prerecorded(source, options)
            return response

    except Exception as e:
        raise Exception(f"Error transcribing audio with Deepgram: {str(e)}")

def get_deepgram_api_key():
    api_key = os.environ.get("DG_API_KEY")
    if not api_key:
        raise ValueError("Deepgram API key not found in environment variables")
    return api_key
