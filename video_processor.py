from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

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

def add_subtitles_to_video(video_path, subtitle_file, output_path, font_color, bg_color, font_size):
    video = VideoFileClip(video_path)
    print(f"Original video resolution: {video.w}x{video.h}")
    
    def create_subtitle_clip(txt, start, end):
        # Base font size
        base_fontsize = 12
        video_height = video.h
        # Scale factor to maintain text proportion
        scale_factor = min(video_height / 1080, 0.5)  # now the max scale is 50%
        adjusted_base_fontsize = int(base_fontsize * scale_factor)
        max_fontsize = int(24 * scale_factor)
        user_scale_factor = font_size / 24
        
        # Calculate font size based on text length
        calculated_fontsize = calculate_font_size(txt, adjusted_base_fontsize, max_fontsize)
        
        # Apply user scale factor and ensure minimum size
        final_fontsize = max(int(calculated_fontsize * user_scale_factor), 5)

        # Adjust the size to fit better
        subtitle_width_factor = 0.8  # increase width factor for better text wrapping
        subtitle_size = (video.w * subtitle_width_factor, None)

        return (TextClip(txt, fontsize=final_fontsize, font='Arial', color=font_color, bg_color=bg_color, size=subtitle_size)
                .set_position(('center', 'bottom'))
                .set_start(start)
                .set_end(end))

    with open(subtitle_file, 'r') as f:
        subtitles = f.read().split('\n\n')

    subtitle_clips = []
    for subtitle in subtitles:
        if subtitle.strip():
            parts = subtitle.split('\n')
            timecode = parts[1].split(' --> ')
            start = time_to_seconds(timecode[0])
            end = time_to_seconds(timecode[1])
            text = ' '.join(parts[2:])
            subtitle_clips.append(create_subtitle_clip(text, start, end))

    final_video = CompositeVideoClip([video] + subtitle_clips)
    print(f"Output video resolution: {final_video.w}x{final_video.h}")
    final_video.write_videofile(output_path, codec='libx264', audio_codec='aac')
    video.close()
    final_video.close()

def time_to_seconds(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)
