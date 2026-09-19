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


def process_uploaded_lecture(
    video_path: str,
    lecture_id: str,
    user_id: str
):
    try:
        process_lecture(
            video_path=video_path,
            lecture_id=lecture_id,
            user_id=user_id
        )

       

    except Exception as error:

        print(
            f"Lecture processing failed "
            f"for {lecture_id}: {error}"
        )

        supabase.table("lectures").update({
            "status": "failed"
        }).eq(
            "id", lecture_id
        ).eq(
            "user_id", user_id
        ).execute()


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
            "id, title, status, duration_seconds, created_at"
        )
        .eq("user_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )

    return {
        "lectures": response.data
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
            "id, title, status, duration_seconds, created_at"
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