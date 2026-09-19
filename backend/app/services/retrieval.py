from app.database.supabase import supabase
from app.services.embeddings import create_embedding


def retrieve_chunks(
    query: str,
    user_id: str,
    lecture_id: str | None = None,
    top_k: int = 5,
    threshold: float = 0.3
):
    query_embedding = create_embedding(query)

    embedding_string = "[" + ",".join(
        map(str, query_embedding)
    ) + "]"

    response = supabase.rpc(
        "match_chunks",
        {
            "query_embedding": embedding_string,
            "match_threshold": threshold,
            "match_count": top_k,
            "filter_user_id": user_id,
            "filter_lecture_id": lecture_id
        }
    ).execute()

    return response.data