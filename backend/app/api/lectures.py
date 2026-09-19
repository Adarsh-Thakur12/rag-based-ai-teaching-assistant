from pathlib import Path
import uuid

from fastapi import APIRouter, BackgroundTasks, File, Form, UploadFile

from app.database.supabase import supabase
from app.services.ingestion import process_lecture


router = APIRouter(prefix="/lectures", tags=["Lectures"])

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

        supabase.table("lectures").update({
            "status": "ready"
        }).eq("id", lecture_id).execute()

    except Exception:
        supabase.table("lectures").update({
            "status": "failed"
        }).eq("id", lecture_id).execute()


@router.post("/upload")
async def upload_lecture(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    user_id: str = Form(...)
):
    lecture_id = str(uuid.uuid4())

    file_extension = Path(file.filename).suffix
    stored_filename = f"{lecture_id}{file_extension}"
    video_path = UPLOAD_DIR / stored_filename

    with open(video_path, "wb") as buffer:
        while chunk := await file.read(1024 * 1024):
            buffer.write(chunk)

    supabase.table("lectures").insert({
        "id": lecture_id,
        "user_id": user_id,
        "title": title,
        "file_path": str(video_path),
        "status": "processing"
    }).execute()

    background_tasks.add_task(
        process_uploaded_lecture,
        str(video_path),
        lecture_id,
        user_id
    )

    return {
        "lecture_id": lecture_id,
        "title": title,
        "status": "processing"
    } 