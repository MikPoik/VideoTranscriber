import os
import time
import logging
from moviepy import VideoFileClip, TextClip, CompositeVideoClip, ImageClip
from moviepy.video.tools.subtitles import SubtitlesClip
from textwrap import wrap
import numpy as np
import random

def extract_audio(video_path, audio_path):
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile(audio_path)
    video.close()
    audio.close()

class SubtitlePosition:
    def __init__(self, width, height, clip_width, clip_height):
        self.width = width
        self.height = height
        self.clip_width = clip_width
        self.clip_height = clip_height
    
    def __call__(self, t):
        return ((self.width - self.clip_width) // 2, self.height - self.clip_height - 50)

def create_subtitle_clip(txt, start, end, video_size, font_color, bg_color, font_size, transparency):
    video_width, video_height = video_size

    fontsize = max(int(font_size * (video_height / 720)), 12)  # Ensure minimum font size of 12
    max_chars_per_line = int(video_width / (fontsize * 0.6))
    wrapped_text = '\n'.join(wrap(txt, max_chars_per_line))
    font_path = os.path.join('fonts', 'LiberationSans-Regular.ttf')
    txt_clip = TextClip(font_path,text=wrapped_text, font_size=fontsize, color=font_color, method='label')
    
    # Create a background with alpha
    bg_color_rgb = tuple(int(bg_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    alpha = int(255 * (1 - transparency/100))  # Convert transparency percentage to alpha value
    color_array = np.full((txt_clip.h + 10, txt_clip.w + 10, 4), (*bg_color_rgb, alpha), dtype=np.uint8)
    color_clip = ImageClip(color_array, transparent=True)
    
    # Overlay the text clip on the color clip
    txt_clip = txt_clip.with_position((5, 5))
    subtitle_clip = CompositeVideoClip([color_clip, txt_clip])
    
    # Create a picklable position handler
    position_handler = SubtitlePosition(video_width, video_height, subtitle_clip.w, subtitle_clip.h)
    
    # Set position using the handler
    subtitle_clip = subtitle_clip.with_position(position_handler)
    subtitle_clip = subtitle_clip.with_start(start).with_end(end)
    
    return subtitle_clip

def create_subtitle_clip_wrapper(txt, start, end, video_dims, font_color, bg_color, font_size, transparency):
    return create_subtitle_clip(txt, start, end, video_dims, font_color, bg_color, font_size, transparency)

def add_subtitles_to_video(video_path, subtitle_file, output_path, font_color, bg_color, font_size, transparency,temp_file_name):
    video = VideoFileClip(video_path)
    print(f"Original video resolution: {video.w}x{video.h}")
    print(temp_file_name)

    subtitles = []
    with open(subtitle_file, 'r') as f:
        content = f.read().strip().split('\n\n')
        for subtitle in content:
            parts = subtitle.split('\n')
            if len(parts) >= 3:  # Ensure we have at least 3 parts (index, timecode, and text)
                timecode = parts[1].split(' --> ')
                start = time_to_seconds(timecode[0])
                end = time_to_seconds(timecode[1])
                text = ' '.join(parts[2:])
                subtitles.append(((start, end), text))

    from multiprocessing import Pool, cpu_count
    # Get CPU count once at the beginning
    processes = cpu_count()

    if subtitles:
        # Create clips in parallel using available CPU cores
        with Pool(processes=processes) as pool:
            subtitle_clips = pool.starmap(
                create_subtitle_clip_wrapper,
                [(sub[1], sub[0][0], sub[0][1], (video.w, video.h), font_color, bg_color, font_size, transparency) for sub in subtitles]
            )
            
        final_video = CompositeVideoClip([video] + subtitle_clips, size=video.size)
    else:
        subtitle_clips = []
        final_video = video

    print(f"Output video resolution: {final_video.w}x{final_video.h}")
    
    # Start timing
    start_time = time.time()
    
    # Optimized write configuration
    final_video.write_videofile(
        output_path,
        preset='ultrafast',
        temp_audiofile=temp_file_name,
        codec='libx264',
        audio_codec='libmp3lame',
        threads=processes,
        ffmpeg_params=['-crf', '28']  # Balanced quality/compression
    )
    
    # Clean up clips to free memory
    for clip in subtitle_clips:
        clip.close()
    
    # Calculate duration
    duration = time.time() - start_time
    logging.info(f"Video write completed in {duration:.2f} seconds")
    
    video.close()
    final_video.close()

def time_to_seconds(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)
