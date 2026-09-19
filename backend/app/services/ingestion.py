import os
from pathlib import Path

from app.database.supabase import supabase

from app.services.video_processor import convert_video_to_mp3
from app.services.transcription import transcribe_audio
from app.services.chunking import create_chunks
from app.services.embeddings import create_embedding
from app.services.chunk_storage import store_chunks


def update_lecture_error(
    lecture_id: str,
    user_id: str,
    error_message: str
):
    supabase.table("lectures").update({
        "status": "failed",
        "error_message": error_message
    }).eq(
        "id", lecture_id
    ).eq(
        "user_id", user_id
    ).execute()


def process_lecture(
    video_path: str,
    lecture_id: str,
    user_id: str
):
    video_path = Path(video_path)

    audio_path = video_path.with_suffix(".mp3")

    try:

        # -------------------------------------------------
        # 1. Start processing
        # -------------------------------------------------

        update_lecture_status(
            lecture_id=lecture_id,
            user_id=user_id,
            status="processing"
        )

        # -------------------------------------------------
        # 2. Convert video to MP3
        # -------------------------------------------------

        convert_video_to_mp3(
            str(video_path),
            str(audio_path)
        )

        # -------------------------------------------------
        # 3. Transcribe audio using Whisper
        # -------------------------------------------------

        update_lecture_status(
            lecture_id=lecture_id,
            user_id=user_id,
            status="transcribing"
        )

        transcription_data = transcribe_audio(
            str(audio_path)
        )
        transcription = transcription_data["result"]

        # -------------------------------------------------
        # 4. Save video duration
        # -------------------------------------------------

        duration = transcription_data["duration"]

        if duration is not None:

            supabase.table("lectures").update({
                "duration_seconds": duration
            }).eq(
                "id", lecture_id
            ).eq(
                "user_id", user_id
            ).execute()

        # -------------------------------------------------
        # 5. Create timestamped chunks
        # -------------------------------------------------

        chunks = create_chunks(
            transcription
        )

        # -------------------------------------------------
        # 6. Generate embeddings
        # -------------------------------------------------

        update_lecture_status(
            lecture_id=lecture_id,
            user_id=user_id,
            status="embedding"
        )

        for chunk in chunks:

            chunk["embedding"] = create_embedding(
                chunk["content"]
            )

        # -------------------------------------------------
        # 7. Store chunks + embeddings
        # -------------------------------------------------

        stored_chunks = store_chunks(
            lecture_id=lecture_id,
            user_id=user_id,
            chunks=chunks
        )

        # -------------------------------------------------
        # 8. Mark lecture as ready
        # -------------------------------------------------

        update_lecture_status(
            lecture_id=lecture_id,
            user_id=user_id,
            status="ready"
        )

        return {
            "lecture_id": lecture_id,
            "chunks_created": len(chunks),
            "chunks_stored": len(stored_chunks),
            "duration_seconds": duration
        }

    except Exception as error:

        update_lecture_error(
            lecture_id=lecture_id,
            user_id=user_id,
            error_message=str(error)
        )

        raise

    finally:

        # Always remove temporary MP3
        if audio_path.exists():
            os.remove(audio_path)