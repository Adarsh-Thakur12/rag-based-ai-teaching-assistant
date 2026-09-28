from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.lectures import router as lectures_router
from app.api.chat import router as chat_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(chat_router)
app.include_router(lectures_router)


@app.get("/")
def root():
    return {"message": "RAG Teaching Assistant API"}


@app.get("/health")
def health():
    return {"status": "healthy"}