
# Video Transcriber and Subtitle Generator

A Streamlit web application that transcribes videos and generates editable subtitles using Deepgram's speech recognition API.

## Features

- Video upload support (MP4 format)
- Audio extraction from video
- Speech transcription in multiple languages
- Editable subtitle timing and text
- Customizable subtitle appearance (font size, colors)
- SRT subtitle file generation
- Final video export with embedded subtitles

## Requirements

- Python 3.11+
- Deepgram API key (set as `DG_API_KEY` in Secrets)

## Dependencies

- deepgram-sdk
- moviepy
- streamlit
- numpy

## Usage

1. Upload a video file (MP4 format)
2. Select the language for transcription (default: Finnish)
3. Choose the transcription model
4. Wait for the transcription process to complete
5. Edit subtitle timings and text if needed
6. Customize subtitle appearance
7. Generate and download the final video with subtitles

## Running the Application

The application runs on port 5000. Click the run button or execute:

```bash
streamlit run main.py --server.port 5000
```

## License

MIT License
