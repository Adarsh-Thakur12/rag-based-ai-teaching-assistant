from pathlib import Path
import uuid

from fastapi import (
    APIRouter,
    BackgroundTasks,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile
)

from app.api.dependencies import get_current_user
from app.database.supabase import supabase
from app.services.ingestion import process_lecture


router = APIRouter(
    prefix="/lectures",
    tags=["Lectures"]
)


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


def claim_lecture_processing(
    lecture_id: str,
    user_id: str
) -> bool:
    response = supabase.rpc(
        "claim_lecture_processing",
        {
            "p_lecture_id": lecture_id,
            "p_user_id": user_id
        }
    ).execute()

    return response.data is True


def process_uploaded_lecture(
    video_path: str,
    lecture_id: str,
    user_id: str
):
    try:
        claimed = claim_lecture_processing(
            lecture_id=lecture_id,
            user_id=user_id
        )

        if not claimed:
            print(
                f"Skipping lecture {lecture_id}: "
                "already claimed or not in uploaded state"
            )
            return

        process_lecture(
            video_path=video_path,
            lecture_id=lecture_id,
            user_id=user_id
        )

    except Exception:
        import logging

        logging.exception(
            "Lecture processing failed for %s",
            lecture_id
        )

        try:
            supabase.table("lectures").update({
                "status": "failed"
            }).eq(
                "id", lecture_id
            ).eq(
                "user_id", user_id
            ).execute()
        except Exception:
            logging.exception(
                "Could not update lecture failure status"
            )


# ---------------------------------------------------------
# UPLOAD LECTURE
# ---------------------------------------------------------

@router.post("/upload")
async def upload_lecture(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    current_user=Depends(get_current_user)
):
    user_id = str(current_user.id)

    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file provided"
        )

    lecture_id = str(uuid.uuid4())

    file_extension = Path(file.filename).suffix.lower()

    allowed_extensions = {
        ".mp4",
        ".mkv",
        ".avi",
        ".mov",
        ".webm"
    }

    if file_extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail="Unsupported video format"
        )

    stored_filename = f"{lecture_id}{file_extension}"

    video_path = UPLOAD_DIR / stored_filename

    try:

        with open(video_path, "wb") as buffer:

            while chunk := await file.read(1024 * 1024):
                buffer.write(chunk)

        response = supabase.table("lectures").insert({
            "id": lecture_id,
            "user_id": user_id,
            "title": title,
            "file_path": str(video_path),
            "status": "uploaded"
        }).execute()

        if not response.data:
            raise Exception("Failed to create lecture record")

        background_tasks.add_task(
            process_uploaded_lecture,
            str(video_path),
            lecture_id,
            user_id
        )

        return {
            "lecture_id": lecture_id,
            "title": title,
            "status": "uploaded"
        }

    except Exception as error:

        if video_path.exists():
            video_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload lecture: {str(error)}"
        )


# ---------------------------------------------------------
# LIST USER'S LECTURES
# ---------------------------------------------------------

@router.get("")
def get_lectures(
    current_user=Depends(get_current_user)
):
    user_id = str(current_user.id)

    response = (
        supabase
        .table("lectures")
        .select(
            "id, title, status, duration_seconds, error_message, created_at"
        )
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return {
        "lectures": response.data
    }


# ---------------------------------------------------------
# RETRY FAILED LECTURE
# ---------------------------------------------------------

@router.post("/{lecture_id}/retry")
def retry_lecture(
    lecture_id: str,
    background_tasks: BackgroundTasks,
    current_user=Depends(get_current_user)
):
    user_id = str(current_user.id)

    # Find the lecture belonging to this user
    response = (
        supabase
        .table("lectures")
        .select("id, file_path, status")
        .eq("id", lecture_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="Lecture not found"
        )

    lecture = response.data

    # Only failed lectures can be retried
    if lecture["status"] != "failed":
        raise HTTPException(
            status_code=409,
            detail="Only failed lectures can be retried"
        )

    file_path = lecture.get("file_path")

    if not file_path or not Path(file_path).is_file():
        raise HTTPException(
            status_code=400,
            detail="Original video file not found. Please upload the lecture again."
        )

    # Atomically claim the failed lecture so concurrent
    # retry requests cannot both schedule processing.
    update_response = (
        supabase
        .table("lectures")
        .update({
            "status": "uploaded",
            "error_message": None
        })
        .eq("id", lecture_id)
        .eq("user_id", user_id)
        .eq("status", "failed")
        .execute()
    )

    if not update_response.data:
        raise HTTPException(
            status_code=409,
            detail="Lecture status changed. Refresh and try again."
        )

    try:
        # Remove any chunks left by an earlier partial attempt.
        (
            supabase
            .table("chunks")
            .delete()
            .eq("lecture_id", lecture_id)
            .eq("user_id", user_id)
            .execute()
        )

        background_tasks.add_task(
            process_uploaded_lecture,
            file_path,
            lecture_id,
            user_id
        )

    except Exception as error:
        # Restore a visible failure state if scheduling setup fails.
        supabase.table("lectures").update({
            "status": "failed",
            "error_message": str(error)
        }).eq(
            "id", lecture_id
        ).eq(
            "user_id", user_id
        ).execute()

        raise HTTPException(
            status_code=500,
            detail="Could not schedule lecture retry"
        )

    return {
        "lecture_id": lecture_id,
        "status": "uploaded",
        "message": "Lecture retry scheduled successfully"
    }

# ---------------------------------------------------------
# GET SINGLE LECTURE
# ---------------------------------------------------------

@router.get("/{lecture_id}")
def get_lecture(
    lecture_id: str,
    current_user=Depends(get_current_user)
):
    user_id = str(current_user.id)

    response = (
        supabase
        .table("lectures")
        .select(
            "id, title, status, duration_seconds, error_message, created_at"
        )
        .eq("id", lecture_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="Lecture not found"
        )

    return response.data


# ---------------------------------------------------------
# DELETE LECTURE
# ---------------------------------------------------------

@router.delete("/{lecture_id}")
def delete_lecture(
    lecture_id: str,
    current_user=Depends(get_current_user)
):
    user_id = str(current_user.id)

    # First find the lecture belonging to this user
    response = (
        supabase
        .table("lectures")
        .select("id, file_path")
        .eq("id", lecture_id)
        .eq("user_id", user_id)
        .maybe_single()
        .execute()
    )

    if not response.data:
        raise HTTPException(
            status_code=404,
            detail="Lecture not found"
        )

    lecture = response.data

    # Delete database record.
    # chunks will be deleted automatically because
    # lecture_id has ON DELETE CASCADE.
    (
        supabase
        .table("lectures")
        .delete()
        .eq("id", lecture_id)
        .eq("user_id", user_id)
        .execute()
    )

    # Delete local video file
    file_path = lecture.get("file_path")

    if file_path:
        video_path = Path(file_path)

        if video_path.exists():
            video_path.unlink()

    return {
        "message": "Lecture deleted successfully",
        "lecture_id": lecture_id
    }
