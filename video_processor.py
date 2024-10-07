import os
from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip, ColorClip
from moviepy.video.tools.subtitles import SubtitlesClip
from textwrap import wrap

# Remove the change_settings import and usage

def extract_audio(video_path, audio_path):
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile(audio_path)
    video.close()
    audio.close()

def create_subtitle_clip(txt, start, end, video_size, font_color, bg_color, font_size):
    video_width, video_height = video_size

    base_fontsize = 24
    scale_factor = min(video_height / 720, 1.0)
    fontsize = int(base_fontsize * scale_factor * (font_size / 24))

    max_chars_per_line = int(video_width / (fontsize * 0.6))
    wrapped_text = '\n'.join(wrap(txt, max_chars_per_line))

    txt_clip = TextClip(wrapped_text, fontsize=fontsize, font='DejaVu-Sans', color=font_color.lstrip('#'), 
                        stroke_color='black', stroke_width=2, method='caption', size=(video_width * 0.9, None))

    bg_clip = ColorClip(size=(txt_clip.w, txt_clip.h), color=bg_color.lstrip('#'))
    bg_clip = bg_clip.set_opacity(0.8)

    subtitle_clip = CompositeVideoClip([bg_clip, txt_clip.set_position('center')])
    subtitle_clip = subtitle_clip.set_position(('center', video_height - subtitle_clip.h - 50))

    return subtitle_clip.set_start(start).set_end(end)

def add_subtitles_to_video(video_path, subtitle_file, output_path, font_color, bg_color, font_size):
    video = VideoFileClip(video_path)
    print(f"Original video resolution: {video.w}x{video.h}")
    
    def create_subtitle_clip_wrapper(txt, start, end):
        return create_subtitle_clip(txt, start, end, (video.w, video.h), font_color, bg_color, font_size)

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

    if subtitles:
        subtitle_clips = [create_subtitle_clip_wrapper(sub[1], sub[0][0], sub[0][1]) for sub in subtitles]
        final_video = CompositeVideoClip([video] + subtitle_clips)
    else:
        final_video = video
    
    print(f"Output video resolution: {final_video.w}x{final_video.h}")
    final_video.write_videofile(output_path, codec='libx264', audio_codec='aac')
    video.close()
    final_video.close()

def time_to_seconds(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)
