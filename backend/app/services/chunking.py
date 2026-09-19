def create_chunks(transcription_result):
    chunks = []

    for segment in transcription_result["segments"]:
        text = segment["text"].strip()

        if not text:
            continue

        chunks.append({
            "start_time": segment["start"],
            "end_time": segment["end"],
            "content": text
        })

    return chunks