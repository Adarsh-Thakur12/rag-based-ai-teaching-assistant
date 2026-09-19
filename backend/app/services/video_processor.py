import subprocess
from pathlib import Path


def convert_video_to_mp3(video_path: str, output_path: str) -> str:
    video_path = Path(video_path)
    output_path = Path(output_path)

    output_path.parent.mkdir(parents=True, exist_ok=True)

    command = [
        "ffmpeg",
        "-i",
        str(video_path),
        "-vn",
        "-acodec",
        "mp3",
        "-y",
        str(output_path),
    ]

    subprocess.run(command, check=True)

    return str(output_path)