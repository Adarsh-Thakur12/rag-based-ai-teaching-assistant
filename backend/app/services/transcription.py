import whisper


MODEL_NAME = "large-v2"


def transcribe_audio(audio_path: str):
    model = whisper.load_model(MODEL_NAME)

    result = model.transcribe(
        audio_path,
        language="hi",
        task="translate"
    )

    return result