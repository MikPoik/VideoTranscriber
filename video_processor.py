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
        base_fontsize = 24  # Set a base font size
        video_height = video.h  # Get the video height
        adjusted_fontsize = int(base_fontsize * (video_height / 1080))  # Adjust font size based on video resolution
        fontsize = max(int(font_size * (adjusted_fontsize / base_fontsize)), 5)  # Scale user-selected font size
        print(f"Video resolution: {video.w}x{video.h}")
        print(f"Adjusted base font size: {adjusted_fontsize}")
        print(f"Final font size: {fontsize}")
        return (TextClip(txt, fontsize=fontsize, font='Arial', color=font_color, bg_color=bg_color, size=(video.w, None))
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
