from numpy import ma
import streamlit as st
import os
from datetime import time
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

# Initialize session state
if 'processed_video' not in st.session_state:
    st.session_state.processed_video = None
if 'transcription' not in st.session_state:
    st.session_state.transcription = None
if 'subtitle_file' not in st.session_state:
    st.session_state.subtitle_file = None
if 'temp_dir' not in st.session_state:
    st.session_state.temp_dir = tempfile.mkdtemp()
if 'temp_video_path' not in st.session_state:
    st.session_state.temp_video_path = None
if 'temp_audio_path' not in st.session_state:
    st.session_state.temp_audio_path = None
if 'language' not in st.session_state:
    st.session_state.language = 'fi'
if 'model' not in st.session_state:
    st.session_state.model = 'whisper-large'
if 'video_duration' not in st.session_state:
    st.session_state.video_duration = 90

async def process_video(temp_video_path, temp_audio_path, temp_dir, progress_bar):
    try:
        transcription = None
        subtitle_file = None
        duration = None

        # Extract audio if not already done
        if not os.path.exists(temp_audio_path):
            progress_bar.progress(0.1)
            with st.spinner("Extracting audio..."):
                await asyncio.to_thread(extract_audio, temp_video_path, temp_audio_path)
            progress_bar.progress(0.3)
            st.success("Audio extraction complete!")
            logger.info("Audio extraction completed successfully")

        # Transcribe audio if not already done
        if transcription is None:
            progress_bar.progress(0.4)
            with st.spinner("Transcribing audio..."):
                transcription_task = asyncio.create_task(transcribe_audio(temp_audio_path,st.session_state.language,st.session_state.model))
                try:
                    transcription, duration = await asyncio.wait_for(transcription_task, timeout=300)  # 5-minute timeout
                    logger.info("Transcription completed successfully")
                except asyncio.TimeoutError:
                    logger.warning("Transcription timed out after 300 seconds")
                    transcription_task.cancel()
                    try:
                        await transcription_task
                    except asyncio.CancelledError:
                        logger.error("Transcription task cancelled due to timeout")
                        st.error("Transcription timed out. Please try again with a shorter video.")
                        return None, None
            progress_bar.progress(0.7)
            st.success("Transcription complete!")

        # Generate subtitles
        if subtitle_file is None:
            progress_bar.progress(0.8)
            with st.spinner("Generating subtitles..."):
                subtitle_file = await asyncio.to_thread(generate_subtitles, transcription, temp_dir)
            st.success("Subtitles generated!")
            logger.info("Subtitles generated successfully")

        return transcription, subtitle_file, duration
    except Exception as e:
        logger.error(f"Error during video processing: {str(e)}", exc_info=True)
        st.error(f"Error during video processing: {str(e)}")
        return None, None

async def main():
    st.title("Instagram Reel Transcriber and Subtitle Generator")
    language = st.text_input("Language for transcription: ", "fi",max_chars=4)
    model = st.selectbox("Select model:", ["whisper-large","whisper-medium","whisper-tiny","nova-2"])
    if st.session_state.language != language:
        st.session_state.language = language
    if st.session_state.model != model:
        st.session_state.model = model
        
    # File uploader
    uploaded_file = st.file_uploader("Upload an Instagram reel video", type=["mp4"])

    if uploaded_file is not None:
        # Check if the uploaded file is different from the previously processed one
        if st.session_state.processed_video != uploaded_file:
            st.session_state.processed_video = uploaded_file
            st.session_state.transcription = None
            st.session_state.subtitle_file = None

            # Save uploaded file temporarily
            if st.session_state.temp_dir:
                for file in os.listdir(st.session_state.temp_dir):
                    os.remove(os.path.join(st.session_state.temp_dir, file))
            else:
                st.session_state.temp_dir = tempfile.mkdtemp()

            st.session_state.temp_video_path = os.path.join(st.session_state.temp_dir, "input_video.mp4")
            with open(st.session_state.temp_video_path, "wb") as f:
                f.write(uploaded_file.getbuffer())

            # Extract audio
            st.session_state.temp_audio_path = os.path.join(st.session_state.temp_dir, "audio.wav")

            # Process video
            progress_bar = st.progress(0)
            st.session_state.transcription, st.session_state.subtitle_file,duration = await process_video(
                st.session_state.temp_video_path, 
                st.session_state.temp_audio_path, 
                st.session_state.temp_dir, 
                progress_bar
            )
            if st.session_state.video_duration != duration:
                st.session_state.video_duration = duration

        def load_subtitles(file_path):
            with open(file_path, 'r') as f:
                content = f.read().strip().split('\n\n')

            subtitles = []
            for subtitle in content:
                lines = subtitle.split('\n')
                if len(lines) >= 3:
                    index = int(lines[0].strip())
                    timecode = lines[1].strip()
                    text = ' '.join(lines[2:])
                    start, end = timecode.split(' --> ')
                    subtitles.append((index, start, end, text))
            return subtitles
            
        def format_time_str(seconds):
            hours = int(seconds // 3600)
            minutes = int((seconds % 3600) // 60)
            seconds = seconds % 60
            return f"{hours:02}:{minutes:02}:{seconds:06.3f}"
            
        def time_to_seconds(time_str):
            h, m, s = time_str.split(':')
            return int(h) * 3600 + int(m) * 60 + float(s)
            
        def save_subtitles(file_path, subtitles):
            with open(file_path, 'w') as f:
                for index, start, end, text in subtitles:
                    f.write(f"{index}\n{start} --> {end}\n{text}\n\n")
                    
        # Assuming subtitle contents are loaded into st.session_state.subtitle_file
        if st.session_state.transcription is not None and st.session_state.subtitle_file is not None:
            # Load subtitles
            subtitles = load_subtitles(st.session_state.subtitle_file)

            st.subheader('Adjust Subtitles')
            edited_subtitles = []
            for index, start, end, text in subtitles:

                # Single slider for adjusting both start and end times
                start_end_seconds = st.slider(
                    f"Timing for Subtitle {index}, original timing: {time_to_seconds(start)} - {time_to_seconds(end)}",
                    0.0, st.session_state.video_duration, 
                    value=(time_to_seconds(start), time_to_seconds(end)), 
                    step=0.01
                )
                # Update timecodes
                start = format_time_str(start_end_seconds[0])
                end = format_time_str(start_end_seconds[1])
                # Subtitle text input
                text = st.text_input(f"Edit text for Subtitle {index}", text)

                # Collect edited subtitles
                edited_subtitles.append((index, start, end, text))

            # Button to save changes
            if st.button("Save Changes"):
                save_subtitles(st.session_state.subtitle_file, edited_subtitles)
                st.success("Subtitles saved successfully.")
                            
            # Download button for subtitles
            with open(st.session_state.subtitle_file, "rb") as file:
                st.download_button(
                    label="Download Subtitles (.srt)",
                    data=file,
                    file_name="subtitles.srt",
                    mime="text/plain"
                )
                
            # Subtitle customization
            st.subheader("Customize Subtitles")
            font_color = st.color_picker("Font Color", "#FFFFFF")
            bg_color = st.color_picker("Background Color", "#000000")
            font_size = st.slider("Font Size", 5, 50, 24)
            
            if st.button("Generate Video with Subtitles"):
                # Add subtitles to video
                progress_bar = st.progress(0)
                progress_bar.progress(0.9)
                with st.spinner("Adding subtitles to video..."):
                    output_video_path = os.path.join(st.session_state.temp_dir, "output_video.mp4")
                    await asyncio.to_thread(add_subtitles_to_video, st.session_state.temp_video_path, st.session_state.subtitle_file, output_video_path, font_color, bg_color, font_size)
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

if __name__ == "__main__":
    asyncio.run(main())
