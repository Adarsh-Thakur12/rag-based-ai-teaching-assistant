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
            "lecture_id": lecture_id,
            "user_id": user_id,
            "content": chunk["content"],
            "start_time": chunk["start_time"],
            "end_time": chunk["end_time"],
            "source_chunk_id": str(index),
            "embedding": "[" + ",".join(map(str, embedding)) + "]"
        })

    if not rows:
        return []

    response = supabase.table("chunks").insert(rows).execute()

    return response.data