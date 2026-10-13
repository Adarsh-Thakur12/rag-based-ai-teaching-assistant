
import logging
import os
from pathlib import Path

from app.database.supabase import supabase
from app.services.video_processor import convert_video_to_mp3
from app.services.transcription import transcribe_audio
from app.services.chunking import create_chunks
from app.services.embeddings import create_embedding
from app.services.chunk_storage import store_chunks


logger = logging.getLogger(__name__)


def update_lecture_status(
    lecture_id: str,
    user_id: str,
    status: str
):
    supabase.table("lectures").update({
        "status": status
    }).eq(
        "id", lecture_id
    ).eq(
        "user_id", user_id
    ).execute()


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
        if not video_path.is_file():
            raise FileNotFoundError(
                f"Lecture video not found: {video_path}"
            )

        update_lecture_status(
            lecture_id=lecture_id,
            user_id=user_id,
            status="processing"
        )

        convert_video_to_mp3(
            str(video_path),
            str(audio_path)
        )

        if not audio_path.is_file() or audio_path.stat().st_size == 0:
            raise RuntimeError(
                "Video conversion did not produce a valid audio file"
            )

        update_lecture_status(
            lecture_id=lecture_id,
            user_id=user_id,
            status="transcribing"
        )

        transcription_data = transcribe_audio(
            str(audio_path)
        )

        transcription = transcription_data["result"]
        duration = transcription_data["duration"]

        chunks = create_chunks(transcription)

        if not chunks:
            raise ValueError(
                "No transcript chunks were generated. "
                "Check that the video contains understandable speech."
            )

        update_lecture_status(
            lecture_id=lecture_id,
            user_id=user_id,
            status="embedding"
        )

        for chunk in chunks:
            chunk["embedding"] = create_embedding(
                chunk["content"]
            )

        stored_chunks = store_chunks(
            lecture_id=lecture_id,
            user_id=user_id,
            chunks=chunks
        )

        if len(stored_chunks) != len(chunks):
            raise RuntimeError(
                "Not all lecture chunks were stored successfully"
            )

        supabase.table("lectures").update({
            "duration_seconds": duration,
            "error_message": None,
            "status": "ready"
        }).eq(
            "id", lecture_id
        ).eq(
            "user_id", user_id
        ).execute()

        return {
            "lecture_id": lecture_id,
            "chunks_created": len(chunks),
            "chunks_stored": len(stored_chunks),
            "duration_seconds": duration
        }

    except Exception as error:
        logger.exception(
            "Lecture processing failed for %s",
            lecture_id
        )

        try:
            update_lecture_error(
                lecture_id=lecture_id,
                user_id=user_id,
                error_message=str(error)[:2000]
            )
        except Exception:
            logger.exception(
                "Could not update failure status for lecture %s",
                lecture_id
            )

        raise

    finally:
        try:
            if audio_path.exists():
                os.remove(audio_path)
        except OSError:
            logger.exception(
                "Could not remove temporary audio file %s",
                audio_path
            )
