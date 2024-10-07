import streamlit as st
import os
from video_processor import extract_audio, add_subtitles_to_video
from subtitle_generator import generate_subtitles
from transcriber import transcribe_audio
import asyncio

st.set_page_config(page_title="Instagram Reel Transcriber", layout="wide")

def initialize_session_state():
    if 'processing_step' not in st.session_state:
        st.session_state.processing_step = 0
    if 'temp_video_path' not in st.session_state:
        st.session_state.temp_video_path = None
    if 'temp_audio_path' not in st.session_state:
        st.session_state.temp_audio_path = None
    if 'transcription' not in st.session_state:
        st.session_state.transcription = None
    if 'subtitle_file' not in st.session_state:
        st.session_state.subtitle_file = None
    if 'output_video_path' not in st.session_state:
        st.session_state.output_video_path = None

def main():
    initialize_session_state()
    
    st.title("Instagram Reel Transcriber and Subtitle Generator")

    uploaded_file = st.file_uploader("Upload an Instagram reel video", type=["mp4"])

    if uploaded_file is not None:
        st.video(uploaded_file)

        # Subtitle customization
        st.subheader("Customize Subtitles")
        font_color = st.color_picker("Font Color", "#FFFFFF")
        bg_color = st.color_picker("Background Color", "#000000")
        font_size = st.slider("Font Size", 5, 50, 24)

        col1, col2 = st.columns(2)
        process_button = col1.button("Process Video")
        regenerate_button = col2.button("Regenerate with New Settings")

        if process_button or regenerate_button:
            if process_button or st.session_state.processing_step == 0:
                st.session_state.processing_step = 0
            
            progress_bar = st.progress(0)
            status_text = st.empty()

            try:
                # Step 1: Save uploaded video
                if st.session_state.processing_step == 0:
                    status_text.text("Saving uploaded video...")
                    temp_video_path = "temp_video.mp4"
                    with open(temp_video_path, "wb") as f:
                        f.write(uploaded_file.getbuffer())
                    st.session_state.temp_video_path = temp_video_path
                    st.session_state.processing_step = 1
                    progress_bar.progress(0.2)

                # Step 2: Extract audio
                if st.session_state.processing_step <= 1:
                    status_text.text("Extracting audio...")
                    temp_audio_path = "temp_audio.wav"
                    extract_audio(st.session_state.temp_video_path, temp_audio_path)
                    st.session_state.temp_audio_path = temp_audio_path
                    st.session_state.processing_step = 2
                    progress_bar.progress(0.4)

                # Step 3: Transcribe audio
                if st.session_state.processing_step <= 2:
                    status_text.text("Transcribing audio...")
                    transcription = asyncio.run(transcribe_audio(st.session_state.temp_audio_path))
                    st.session_state.transcription = transcription
                    st.session_state.processing_step = 3
                    progress_bar.progress(0.6)

                # Step 4: Generate subtitles
                if st.session_state.processing_step <= 3:
                    status_text.text("Generating subtitles...")
                    subtitle_file = generate_subtitles(st.session_state.transcription, ".")
                    st.session_state.subtitle_file = subtitle_file
                    st.session_state.processing_step = 4
                    progress_bar.progress(0.8)

                # Step 5: Add subtitles to video
                if st.session_state.processing_step <= 4:
                    status_text.text("Adding subtitles to video...")
                    output_video_path = "output_video.mp4"
                    add_subtitles_to_video(st.session_state.temp_video_path, st.session_state.subtitle_file, output_video_path, font_color, bg_color, font_size)
                    st.session_state.output_video_path = output_video_path
                    st.session_state.processing_step = 5
                    progress_bar.progress(1.0)

                if st.session_state.processing_step == 5:
                    status_text.text("Video processing complete!")
                    st.video(st.session_state.output_video_path)
                    
                    with open(st.session_state.output_video_path, "rb") as file:
                        st.download_button(
                            label="Download Video with Subtitles",
                            data=file,
                            file_name="subtitled_video.mp4",
                            mime="video/mp4"
                        )
            except Exception as e:
                st.error(f"An error occurred: {str(e)}")
                st.session_state.processing_step = 0

if __name__ == "__main__":
    main()
