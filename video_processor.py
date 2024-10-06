from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

def extract_audio(video_path, audio_path):
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile(audio_path)
    video.close()
    audio.close()

def add_subtitles_to_video(video_path, subtitle_file, output_path, font_color, bg_color, font_size):
    video = VideoFileClip(video_path)
    print(f"Original video resolution: {video.w}x{video.h}")
    
    def create_subtitle_clip(txt, start, end):
        base_fontsize = 12  # Set a smaller base font size
        video_height = video.h  # Get the video height
        scale_factor = min(video_height / 1080, 1.0)  # Limit the scale factor to a maximum of 1.0
        adjusted_fontsize = int(base_fontsize * scale_factor)  # Adjust base font size
        user_scale_factor = font_size / 24  # Calculate user scale factor (24 is the default in the UI)
        final_fontsize = min(max(int(adjusted_fontsize * user_scale_factor), 5), 36)  # Apply user scale, ensure minimum size of 5 and maximum size of 36
        
        print(f"Video resolution: {video.w}x{video.h}")
        print(f"Scale factor: {scale_factor}")
        print(f"Adjusted base font size: {adjusted_fontsize}")
        print(f"User-selected font size: {font_size}")
        print(f"User scale factor: {user_scale_factor}")
        print(f"Final font size: {final_fontsize}")
        
        return (TextClip(txt, fontsize=final_fontsize, font='Arial', color=font_color, bg_color=bg_color, size=(video.w * 0.8, None))
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
