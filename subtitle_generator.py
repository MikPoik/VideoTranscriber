import os

def generate_subtitles(transcription, output_dir):
    subtitle_file = os.path.join(output_dir, "subtitles.srt")

    with open(subtitle_file, "w") as f:
        paragraphs = transcription["results"]["channels"][0]["alternatives"][0]["paragraphs"]["paragraphs"]

        index = 1
        for paragraph in paragraphs:
            sentences = paragraph["sentences"]
            for sentence in sentences:
                start_time = format_time(sentence["start"])
                end_time = format_time(sentence["end"])
                text = sentence["text"]
                f.write(f"{index}\n")
                f.write(f"{start_time} --> {end_time}\n")
                f.write(f"{text}\n\n")
                index += 1

    return subtitle_file
def format_time(seconds):
    hours = int(seconds / 3600)
    minutes = int((seconds % 3600) / 60)
    seconds = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{seconds:06.3f}"
