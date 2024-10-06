import streamlit as st
import os
import tempfile
import asyncio
from video_processor import extract_audio, add_subtitles_to_video
from subtitle_generator import generate_subtitles
from transcriber import transcribe_audio

st.set_page_config(page_title="Instagram Reel Transcriber", layout="wide")

async def process_video(temp_video_path, temp_audio_path, temp_dir):
    # Extract audio
    await asyncio.to_thread(extract_audio, temp_video_path, temp_audio_path)

    # Transcribe audio
    try:
        with st.spinner("Transcribing audio..."):
            transcription = await transcribe_audio(temp_audio_path)
        st.success("Transcription complete!")
    except Exception as e:
        st.error(f"Error during transcription: {str(e)}")
        return None

    return transcription

async def main():
    st.title("Instagram Reel Transcriber and Subtitle Generator")

    # File uploader
    uploaded_file = st.file_uploader("Upload an Instagram reel video", type=["mp4"])

    if uploaded_file is not None:
        # Save uploaded file temporarily
        temp_dir = tempfile.mkdtemp()
        temp_video_path = os.path.join(temp_dir, "input_video.mp4")
        with open(temp_video_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Extract audio
        temp_audio_path = os.path.join(temp_dir, "audio.wav")

        # Process video
        transcription = await process_video(temp_video_path, temp_audio_path, temp_dir)

        if transcription is not None:
            # Subtitle customization
            st.subheader("Customize Subtitles")
            font_color = st.color_picker("Font Color", "#FFFFFF")
            bg_color = st.color_picker("Background Color", "#000000")
            font_size = st.slider("Font Size", 5, 50, 24)

            # Generate subtitles
            subtitle_file = await asyncio.to_thread(generate_subtitles, transcription, temp_dir)

            # Add subtitles to video
            output_video_path = os.path.join(temp_dir, "output_video.mp4")
            await asyncio.to_thread(add_subtitles_to_video, temp_video_path, subtitle_file, output_video_path, font_color, bg_color, font_size)

            # Display video preview
            st.subheader("Video Preview")
            st.video(output_video_path)

            # Download button
            with open(output_video_path, "rb") as file:
                st.download_button(
                    label="Download Video with Subtitles",
                    data=file,
                    file_name="subtitled_video.mp4",
                    mime="video/mp4"
                )

            # Clean up temporary files
            await asyncio.to_thread(os.remove, temp_video_path)
            await asyncio.to_thread(os.remove, temp_audio_path)
            await asyncio.to_thread(os.remove, subtitle_file)
            await asyncio.to_thread(os.remove, output_video_path)
            await asyncio.to_thread(os.rmdir, temp_dir)

if __name__ == "__main__":
    asyncio.run(main())
