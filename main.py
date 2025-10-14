import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from routes.conversation_routes import router as conversation_router
from routes.message_routes import router as message_router
from routes.document_routes import router as document_router

load_dotenv()
app = FastAPI(title="Knowledge Base Search Engine")

# ---- CORS (allow your frontend) ----
# Replace origins list with your actual frontend origins (dev + prod)
default_origins = [
    "http://localhost:3000",
    "*",
]

raw_origins = os.getenv("CORS_ORIGINS")
if raw_origins:
    origins = [
        origin.strip().rstrip("/")
        for origin in raw_origins.split(",")
        if origin.strip()
    ]
    if not origins:
        origins = ["*"]
else:
    origins = default_origins

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if "*" not in origins else ["*"],  # or allow_origin_regex=".*" for dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"], # optional, if you serve file downloads
)

# ---- Routers ----
app.include_router(conversation_router, prefix="/conversations", tags=["Conversations"])
app.include_router(message_router, prefix="/conversations", tags=["Messages"])
app.include_router(document_router, prefix="/conversations", tags=["Documents"])

@app.get("/health")
def health():
    return {"status": "Backend running ✅"}

@app.get("/")
def root():
    return {"status": "Backend running ✅"}
