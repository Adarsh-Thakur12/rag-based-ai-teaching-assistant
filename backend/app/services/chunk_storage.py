
from app.database.supabase import supabase


def store_chunks(
    lecture_id: str,
    user_id: str,
    chunks: list[dict]
):
    rows = []

    for index, chunk in enumerate(chunks):
        embedding = chunk["embedding"]

        rows.append({
            "content": chunk["content"],
            "start_time": chunk["start_time"],
            "end_time": chunk["end_time"],
            "source_chunk_id": str(index),
            "embedding": "[" + ",".join(
                map(str, embedding)
            ) + "]"
        })

    response = supabase.rpc(
        "replace_lecture_chunks",
        {
            "p_lecture_id": lecture_id,
            "p_user_id": user_id,
            "p_chunks": rows
        }
    ).execute()

    stored_count = response.data

    if stored_count != len(chunks):
        raise RuntimeError(
            f"Expected {len(chunks)} chunks, "
            f"but stored {stored_count}"
        )

    return rows
