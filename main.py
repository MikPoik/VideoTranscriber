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
from streamlit_chunk_file_uploader import uploader
import random

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
if 'output_video_path' not in st.session_state:
    st.session_state.output_video_path = None
if 'processing_completed' not in st.session_state:
        st.session_state.processing_completed = False
if 'can_process' not in st.session_state:
    st.session_state.can_process = True
if 'video_ready' not in st.session_state:
    st.session_state.video_ready = False
if 'temp_audio_file' not in st.session_state:
    st.session_state.temp_audio_file = str(random.randint(1000, 10000))+".mp3"

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
    st.title("Video transcriber and subtitle generator")
    language = st.text_input("Language for transcription: ", "fi",max_chars=4)
    model = st.selectbox("Select model:", ["whisper-large","whisper-medium","whisper-tiny","nova-2"])
    if st.session_state.language != language:
        st.session_state.language = language
    if st.session_state.model != model:
        st.session_state.model = model

    # File uploader
    uploaded_file = uploader("uploader", key="chunk_uploader", chunk_size=31)

    if uploaded_file is not None:
        # Check if the uploaded file is different from the previously processed one
        if st.session_state.processed_video != uploaded_file:
            st.session_state.processed_video = uploaded_file
            st.session_state.transcription = None
            st.session_state.subtitle_file = None
            st.session_state.can_process = False
            st.session_state.can_process = True
            st.session_state.video_ready = False
            st.session_state.last_file_size = None
            st.session_state.processing_status = ""
            st.session_state.temp_audio_file = str(random.randint(1000, 10000))+".mp3"

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
            
            # Create raw subtitle content for editing
            current_content = ""
            for index, start, end, text in subtitles:
                current_content += f"{index}\n{start} --> {end}\n{text}\n\n"
            
            # Add expander for raw subtitle editing
            with st.expander("Edit Subtitle Timings"):
                edited_content = st.text_area("Edit subtitle timings directly", current_content, height=300)
            
            # Parse the edited content
            try:
                edited_blocks = edited_content.strip().split('\n\n')
                for block in edited_blocks:
                    lines = block.strip().split('\n')
                    if len(lines) >= 3:
                        index = int(lines[0].strip())
                        timecode = lines[1].strip()
                        text = '\n'.join(lines[2:])
                        start, end = timecode.split(' --> ')
                        
                        # Add text input for each subtitle
                        text = st.text_input(f"Subtitle {index} text:", text, label_visibility="visible")
                        
                        edited_subtitles.append((index, start, end, text))
            except Exception as e:
                st.error("Error parsing subtitle format. Please ensure correct format: index, timecode, text")

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
            transparency = st.slider("Background Transparency", 0, 100, 50)

            # Initialize states
            if 'can_process' not in st.session_state:
                st.session_state.can_process = True
            if 'last_file_size' not in st.session_state:
                st.session_state.last_file_size = None
            if 'processing_status' not in st.session_state:
                st.session_state.processing_status = ""

            # Create status containers
            status_container = st.empty()
            preview_container = st.container()

            @st.fragment(run_every=3)
            def check_video_status(temp_filename):
                output_video_path = os.path.join(st.session_state.temp_dir, "output_video.mp4")
                
                if os.path.exists(output_video_path):
                    current_size = os.path.getsize(output_video_path)

                    # If size changed or processing just completed
                    if st.session_state.last_file_size != current_size or st.session_state.processing_completed:
                        st.session_state.last_file_size = current_size
                        st.session_state.processing_completed = False
                        output_temp_audiofile_path = os.path.join(os.getcwd(), st.session_state.temp_audio_file)

                        if not os.path.exists(output_temp_audiofile_path):
                            st.session_state.processing_status = "Video processing complete!"
                            st.rerun()
                    return True
                return False
                

            # Initialize generate state
            if 'generate_video' not in st.session_state:
                st.session_state.generate_video = False

            def trigger_generation():
                st.session_state.generate_video = True
                st.session_state.can_process = False
                st.session_state.video_ready = False
                st.session_state.last_file_size = None

            # Generate button

            st.button("Generate/Regenerate Video", key="generate_button", on_click=trigger_generation)

            # Handle video generation based on state
            if st.session_state.generate_video and not st.session_state.can_process:
                output_video_path = os.path.join(st.session_state.temp_dir, "output_video.mp4")
                if not os.path.exists(st.session_state.temp_audio_file):
                    st.session_state.temp_audio_file = str(random.randint(1000, 10000)) + ".mp3"
                    
                output_temp_audiofile_path = os.path.join(os.getcwd(), st.session_state.temp_audio_file)

                # Check if video needs to be generated
                needs_processing = True
                if os.path.exists(output_video_path):
                    current_size = os.path.getsize(output_video_path)

                    if os.path.exists(output_temp_audiofile_path):
                        print("temp_file_exists")
                        needs_processing = False

                    if st.session_state.last_file_size == current_size:
                        print("Video already generated")
                        needs_processing = False
                
                if needs_processing:
                    st.session_state.processing_status = "Processing video..."
                    status_placeholder = st.empty()
                    status_placeholder.info("Processing video... This might take a while..")
                    progress_bar = st.progress(0)
                    progress_bar.progress(0.9)
                    st.session_state.processing_completed = False

                    
                    try:
                        await asyncio.wait_for(
                            asyncio.to_thread(add_subtitles_to_video, 
                                st.session_state.temp_video_path, 
                                st.session_state.subtitle_file, 
                                output_video_path, 
                                font_color, 
                                bg_color, 
                                font_size, 
                                transparency,
                                output_temp_audiofile_path),
                            timeout=600
                        )
                        progress_bar.progress(1.0)
                        st.session_state.processing_status = "Video processing complete!"
                        st.session_state.last_file_size = os.path.getsize(output_video_path)
                        st.session_state.video_ready = True
                        st.session_state.processing_completed = True
                        logger.info("Video processing completed successfully")
                    except asyncio.TimeoutError:
                        st.session_state.processing_status = "Video processing timed out. Try with a smaller video."
                        logger.error("Video processing timed out")
                    except Exception as e:
                        st.session_state.processing_status = f"Error during video processing: {str(e)}"
                        logger.error(f"Error during video processing: {str(e)}")                    
                    st.session_state.generate_video = False
                    st.session_state.can_process = True
                    st.session_state.video_ready = True
                    st.rerun()

            # Update status message
            with status_container:
                if st.session_state.processing_status:
                    if "complete" in st.session_state.processing_status.lower():
                        st.success(st.session_state.processing_status)
                    elif "error" in st.session_state.processing_status.lower() or "timed out" in st.session_state.processing_status.lower():
                        st.error(st.session_state.processing_status)
                    else:
                        st.info(st.session_state.processing_status)

            # Show video preview and download button if video is ready
            is_ready = check_video_status(st.session_state.temp_audio_file)
            if is_ready or st.session_state.video_ready:
                print("video preview ready")
                output_video_path = os.path.join(st.session_state.temp_dir, "output_video.mp4")
                if os.path.exists(output_video_path):
                    print("video file exists")
                    with preview_container:
                        st.empty()  # Clear previous content
                        st.subheader("Video Preview")
                        st.video(output_video_path)

                        with open(output_video_path, "rb") as file:
                            st.download_button(
                                label="Download Video with Subtitles",
                                data=file,
                                file_name="subtitled_video.mp4",
                                mime="video/mp4"
                            )

if __name__ == "__main__":
    asyncio.run(main())