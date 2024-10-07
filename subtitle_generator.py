import os

def generate_subtitles(transcription, output_dir):
    print("Generating subtitles...")
    subtitle_file = os.path.join(output_dir, "subtitles.srt")
    
    with open(subtitle_file, "w") as f:
        for i, result in enumerate(transcription["results"]["channels"][0]["alternatives"][0]["words"], start=1):
            start_time = format_time(result["start"])
            end_time = format_time(result["end"])
            word = result["word"]
            
            f.write(f"{i}\n")
            f.write(f"{start_time} --> {end_time}\n")
            f.write(f"{word}\n\n")
    
    return subtitle_file

def format_time(seconds):
    hours = int(seconds / 3600)
    minutes = int((seconds % 3600) / 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
