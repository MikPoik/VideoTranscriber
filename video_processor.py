import os
import time
import logging
import subprocess
from multiprocessing import cpu_count

# Get CPU count once at the beginning
processes = cpu_count()

def extract_audio(video_path, audio_path):
    cmd = [
        'ffmpeg', '-y','-i', video_path,
        '-vn', '-acodec', 'pcm_s16le',
        '-ar', '44100', '-ac', '2',
        audio_path
    ]
    subprocess.run(cmd, check=True)

def add_subtitles_to_video(video_path, subtitle_file, output_path, font_color, bg_color, font_size, transparency, temp_file_name):
    # Convert hex colors to RGB format for FFmpeg
    font_color = font_color.lstrip('#')
    bg_color = bg_color.lstrip('#')

    # Calculate background alpha (transparency)
    alpha = hex(int(255 * (1 - transparency/100)))[2:].zfill(2)

    # FFmpeg subtitle style
    font_path = os.path.join(os.getcwd(), 'fonts', 'LiberationSans-Regular.ttf')
    style = f"FontName=LiberationSans-Regular,FontFile={font_path},FontSize={font_size},PrimaryColour=&H{font_color},BackColour=&H{alpha}{bg_color}"

    cmd = [
        'ffmpeg', '-y','-i', video_path,
        '-vf', f"subtitles={subtitle_file}:force_style='{style}'",
        '-c:v', 'libx264', '-preset', 'ultrafast', '-crf', '28',
        '-c:a', 'copy',
        '-threads', str(processes),
        output_path
    ]

    start_time = time.time()
    subprocess.run(cmd, check=True)
    duration = time.time() - start_time
    logging.info(f"Video write completed in {duration:.2f} seconds")

def time_to_seconds(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)