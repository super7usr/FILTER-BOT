import os, time, asyncio, subprocess, json, requests
import subprocess

def check_ffprobe():
    try:
        subprocess.run(["ffprobe", "-version"], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("ffprobe is installed and accessible.")
    except subprocess.CalledProcessError as e:
        print("ffprobe is not installed or not accessible.")
        print("Error:", e)
        # Handle the error or provide instructions to install ffprobe
        print("Please install ffprobe by following the instructions at https://ffmpeg.org/download.html")


def metadata_text():
    author = '❁✗❍═❰ 🆁︎🅴︎🅽︎🅸︎🆂︎🅷︎ ❱═❍✗❁'
    title = '❁✗❍═❰ 🆁︎🅴︎🅽︎🅸︎🆂︎🅷︎ ❱═❍✗❁'
    video_title = '❁✗❍═❰ 🆁︎🅴︎🅽︎🅸︎🆂︎🅷︎ ❱═❍✗❁'
    audio_title = '❁✗❍═❰ 🆁︎🅴︎🅽︎🅸︎🆂︎🅷︎ ❱═❍✗❁'
    subtitle_title = '❁✗❍═❰ 🆁︎🅴︎🅽︎🅸︎🆂︎🅷︎ ❱═❍✗❁'

    return author, title, video_title, audio_title, subtitle_title

def change_metadata(input_file):
    check_ffprobe()
    author, title, video_title, audio_title, subtitle_title = metadata_text()
    output_file = f'Metadata/{input_file}'
    # Get the video metadata
    output = subprocess.check_output(['ffprobe', '-v', 'error', '-show_streams', '-print_format', 'json', input_file])
    data = json.loads(output)
    streams = data['streams']

    # Create the FFmpeg command to change metadata
    cmd = [
        'ffmpeg',
        '-i', input_file,
        '-map', '0',  # Map all streams
        '-c:v', 'copy',  # Copy video stream
        '-c:a', 'copy',  # Copy audio stream
        '-c:s', 'copy',  # Copy subtitles stream
        '-metadata', f'title={title}',
        '-metadata', f'author={author}',
    ]

    # Add title to video stream
    for stream in streams:
        if stream['codec_type'] == 'video' and video_title:
            cmd.extend([f'-metadata:s:{stream["index"]}', f'title={video_title}'])
        elif stream['codec_type'] == 'audio' and audio_title:
            cmd.extend([f'-metadata:s:{stream["index"]}', f'title={audio_title}'])
        elif stream['codec_type'] == 'subtitle' and subtitle_title:
            cmd.extend([f'-metadata:s:{stream["index"]}', f'title={subtitle_title}'])

    cmd.extend(['-metadata', f'comment=Added by @Digital_Rename_Bot'])
    cmd.extend(['-f', 'matroska']) # support all format 
    cmd.append(output_file)
    print(cmd)
    
    # Execute the command
    try:
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print("FFmpeg Error:", e.stderr)
        return False
