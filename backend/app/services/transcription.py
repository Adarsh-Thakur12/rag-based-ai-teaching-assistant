import subprocess

import whisper


MODEL_NAME = "large-v2"


def get_audio_duration(audio_path: str) -> float:
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration",
            "-of",
            "default=noprint_wrappers=1:nokey=1",
            audio_path
        ],
        capture_output=True,
        text=True,
        check=True
    )

    return float(result.stdout.strip())


def transcribe_audio(audio_path: str):

    model = whisper.load_model(MODEL_NAME)

    result = model.transcribe(
        audio_path,
        language="hi",
        task="translate"
    )

    duration = get_audio_duration(audio_path)

    return {
        "result": result,
        "duration": duration
    }