from moviepy.editor import VideoFileClip, TextClip, CompositeVideoClip

def extract_audio(video_path, audio_path):
    video = VideoFileClip(video_path)
    audio = video.audio
    audio.write_audiofile(audio_path)
    video.close()
    audio.close()

def add_subtitles_to_video(video_path, subtitle_file, output_path, font_color, bg_color, font_size):
    video = VideoFileClip(video_path)
    
    def create_subtitle_clip(txt, start, end):
        fontsize = max(int(font_size), 5)  # Ensure minimum font size of 5 and convert to integer
        print(f"Creating subtitle clip with font size: {fontsize}")
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
    final_video.write_videofile(output_path, codec='libx264', audio_codec='aac')
    video.close()
    final_video.close()

def time_to_seconds(time_str):
    h, m, s = time_str.split(':')
    return int(h) * 3600 + int(m) * 60 + float(s)
