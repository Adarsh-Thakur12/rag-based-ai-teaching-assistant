import os
from pathlib import Path

from app.services.video_processor import convert_video_to_mp3
from app.services.transcription import transcribe_audio
from app.services.chunking import create_chunks
from app.services.embeddings import create_embedding
from app.services.chunk_storage import store_chunks


def process_lecture(
    video_path: str,
    lecture_id: str,
    user_id: str
):
    video_path = Path(video_path)

    # 1. Convert video to MP3
    audio_path = video_path.with_suffix(".mp3")

    convert_video_to_mp3(
        str(video_path),
        str(audio_path)
    )

    # 2. Transcribe audio using Whisper
    transcription = transcribe_audio(
        str(audio_path)
    )

    # 3. Create timestamped chunks
    chunks = create_chunks(
        transcription
    )

    # 4. Generate embedding for every chunk
    for chunk in chunks:
        chunk["embedding"] = create_embedding(
            chunk["content"]
        )

    # 5. Store chunks + embeddings in Supabase
    stored_chunks = store_chunks(
        lecture_id=lecture_id,
        user_id=user_id,
        chunks=chunks
    )

    # 6. Remove temporary MP3
    if audio_path.exists():
        os.remove(audio_path)

    return {
        "lecture_id": lecture_id,
        "chunks_created": len(chunks),
        "chunks_stored": len(stored_chunks)
    }