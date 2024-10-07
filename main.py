import streamlit as st
import os
import tempfile
import asyncio
import logging
from video_processor import extract_audio, add_subtitles_to_video
from subtitle_generator import generate_subtitles
from transcriber import transcribe_audio

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Instagram Reel Transcriber", layout="wide")

async def process_video(temp_video_path, temp_audio_path, temp_dir, progress_bar):
    try:
        # Extract audio
        progress_bar.progress(0.1)
        with st.spinner("Extracting audio..."):
            await asyncio.to_thread(extract_audio, temp_video_path, temp_audio_path)
        progress_bar.progress(0.3)
        st.success("Audio extraction complete!")
        logger.info("Audio extraction completed successfully")

        # Transcribe audio
        progress_bar.progress(0.4)
        with st.spinner("Transcribing audio..."):
            transcription_task = asyncio.create_task(transcribe_audio(temp_audio_path))
            try:
                transcription = await asyncio.wait_for(transcription_task, timeout=300)  # 5-minute timeout
                logger.info("Transcription completed successfully")
            except asyncio.TimeoutError:
                logger.warning("Transcription timed out after 300 seconds")
                transcription_task.cancel()
                try:
                    await transcription_task
                except asyncio.CancelledError:
                    logger.error("Transcription task cancelled due to timeout")
                    st.error("Transcription timed out. Please try again with a shorter video.")
                    return None
        progress_bar.progress(0.7)
        st.success("Transcription complete!")

        return transcription
    except Exception as e:
        logger.error(f"Error during video processing: {str(e)}", exc_info=True)
        st.error(f"Error during video processing: {str(e)}")
        return None

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
        progress_bar = st.progress(0)
        transcription = await process_video(temp_video_path, temp_audio_path, temp_dir, progress_bar)

        if transcription is not None:
            # Subtitle customization
            st.subheader("Customize Subtitles")
            font_color = st.color_picker("Font Color", "#FFFFFF")
            bg_color = st.color_picker("Background Color", "#000000")
            font_size = st.slider("Font Size", 5, 50, 24)

            # Generate subtitles
            progress_bar.progress(0.8)
            with st.spinner("Generating subtitles..."):
                subtitle_file = await asyncio.to_thread(generate_subtitles, transcription, temp_dir)
            st.success("Subtitles generated!")
            logger.info("Subtitles generated successfully")

            # Display subtitle content
            with open(subtitle_file, 'r') as f:
                subtitle_content = f.read()
            st.subheader('Generated Subtitles')
            st.text_area('Subtitle Content (.srt)', subtitle_content, height=300)

            # Add subtitles to video
            progress_bar.progress(0.9)
            with st.spinner("Adding subtitles to video..."):
                output_video_path = os.path.join(temp_dir, "output_video.mp4")
                await asyncio.to_thread(add_subtitles_to_video, temp_video_path, subtitle_file, output_video_path, font_color, bg_color, font_size)
            progress_bar.progress(1.0)
            st.success("Video processing complete!")
            logger.info("Video processing completed successfully")

            # Display video preview
            st.subheader("Video Preview")
            st.video(output_video_path)

            # Download button for video
            with open(output_video_path, "rb") as file:
                st.download_button(
                    label="Download Video with Subtitles",
                    data=file,
                    file_name="subtitled_video.mp4",
                    mime="video/mp4"
                )

            # Download button for subtitles
            with open(subtitle_file, "rb") as file:
                st.download_button(
                    label="Download Subtitles (.srt)",
                    data=file,
                    file_name="subtitles.srt",
                    mime="text/plain"
                )

            # Clean up temporary files
            await asyncio.to_thread(os.remove, temp_video_path)
            await asyncio.to_thread(os.remove, temp_audio_path)
            await asyncio.to_thread(os.remove, subtitle_file)
            await asyncio.to_thread(os.remove, output_video_path)
            await asyncio.to_thread(os.rmdir, temp_dir)
            logger.info("Temporary files cleaned up")

if __name__ == "__main__":
    asyncio.run(main())
