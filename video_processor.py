from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip
from moviepy.video.tools.subtitles import SubtitlesClip
from textwrap import wrap

def extract_audio(video_path, audio_path):
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile(audio_path)
    video.close()
    audio.close()

def calculate_font_size(text, base_size, max_size):
    text_length = len(text)
    if text_length <= 5:
        return max_size
    elif text_length <= 20:
        return max(base_size, int(max_size * (1 - (text_length - 5) / 15)))
    else:
        return base_size

def create_subtitle_clip(txt, start, end, video_size, font_color, bg_color, font_size):
    video_width, video_height = video_size

    # Base font size
    base_fontsize = 12
    # Scale factor to maintain text proportion
    scale_factor = min(video_height / 1080, 0.5)  # max scale is 50%
    adjusted_base_fontsize = int(base_fontsize * scale_factor)
    max_fontsize = int(24 * scale_factor)
    user_scale_factor = font_size / 24
    
    # Calculate font size based on text length
    calculated_fontsize = calculate_font_size(txt, adjusted_base_fontsize, max_fontsize)
    
    # Apply user scale factor and ensure minimum size
    final_fontsize = max(int(calculated_fontsize * user_scale_factor), 5)

    # Improve text wrapping
    max_chars_per_line = int(video_width / (final_fontsize * 0.6))  # Estimate chars that fit in video width
    wrapped_text = '\n'.join(wrap(txt, max_chars_per_line))

    # Create text clip with outline
    txt_clip = TextClip(wrapped_text, fontsize=final_fontsize, font='Arial', color=font_color, bg_color=bg_color, 
                        stroke_color='black', stroke_width=2, method='caption', size=(video_width * 0.9, None))
    
    # Position the subtitle at the bottom with some padding
    txt_clip = txt_clip.set_position(('center', video_height - txt_clip.h - 50))
    
    # Set the duration of the subtitle clip
    txt_clip = txt_clip.set_duration(end - start)

    return txt_clip.set_start(start).set_end(end)

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
