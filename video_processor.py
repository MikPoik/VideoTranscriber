import os
import logging
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ImageClip
from moviepy.video.tools.subtitles import SubtitlesClip
from textwrap import wrap
import numpy as np

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def extract_audio(video_path, audio_path):
    print("Extracitng audio from video...")
    try:
        video = VideoFileClip(video_path)
        audio = video.audio
        audio.write_audiofile(audio_path)
        video.close()
        audio.close()
        logger.info(f"Audio extracted successfully from {video_path}")
    except Exception as e:
        logger.error(f"Error extracting audio: {str(e)}")
        raise

def create_subtitle_clip(txt, start, end, video_size, font_color, bg_color, font_size):
    video_width, video_height = video_size

    fontsize = max(int(font_size * (video_height / 720)), 12)  # Ensure minimum font size of 12
    max_chars_per_line = int(video_width / (fontsize * 0.6))
    wrapped_text = '\n'.join(wrap(txt, max_chars_per_line))

    txt_clip = TextClip(wrapped_text, fontsize=fontsize, font='Arial', color=font_color, method='label')
    
    # Optimize color conversion
    bg_color_rgb = tuple(int(bg_color.lstrip('#')[i:i+2], 16) for i in (0, 2, 4))
    color_array = np.full((txt_clip.h + 10, txt_clip.w + 10, 3), bg_color_rgb, dtype=np.uint8)
    color_clip = ImageClip(color_array)
    
    txt_clip = txt_clip.set_position((5, 5))
    subtitle_clip = CompositeVideoClip([color_clip, txt_clip])
    
    subtitle_clip = subtitle_clip.set_position(('center', video_height - subtitle_clip.h - 50))

    return subtitle_clip.set_start(start).set_end(end)

def subtitle_clips_generator(subtitles, video_size, font_color, bg_color, font_size):
    for start, end, text in subtitles:
        yield create_subtitle_clip(text, start, end, video_size, font_color, bg_color, font_size)

def add_subtitles_to_video(video_path, subtitle_file, output_path, font_color, bg_color, font_size):
    try:
        video = VideoFileClip(video_path)
        logger.info(f"Original video resolution: {video.w}x{video.h}")
        
        subtitles = parse_subtitles(subtitle_file)
        
        if subtitles:
            subtitle_clips = subtitle_clips_generator(subtitles, (video.w, video.h), font_color, bg_color, font_size)
            final_video = CompositeVideoClip([video] + list(subtitle_clips), size=video.size)
        else:
            logger.warning("No subtitles found. Output video will be identical to input.")
            final_video = video
        
        logger.info(f"Output video resolution: {final_video.w}x{final_video.h}")
        final_video.write_videofile(output_path, codec='libx264', audio_codec='aac')
        video.close()
        final_video.close()
        logger.info(f"Video with subtitles saved to {output_path}")
    except Exception as e:
        logger.error(f"Error adding subtitles to video: {str(e)}")
        raise

def parse_subtitles(subtitle_file):
    subtitles = []
    try:
        with open(subtitle_file, 'r') as f:
            content = f.read().strip().split('\n\n')
            for subtitle in content:
                parts = subtitle.split('\n')
                if len(parts) >= 3:
                    timecode = parts[1].split(' --> ')
                    start = time_to_seconds(timecode[0])
                    end = time_to_seconds(timecode[1])
                    text = ' '.join(parts[2:])
                    subtitles.append((start, end, text))
        logger.info(f"Parsed {len(subtitles)} subtitles from {subtitle_file}")
        return subtitles
    except Exception as e:
        logger.error(f"Error parsing subtitles: {str(e)}")
        return []

def time_to_seconds(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)
