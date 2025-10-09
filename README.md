# Backend – FastAPI Service

This directory contains the Retrieval-Augmented Generation (RAG) API that powers the Knowledge-Based Search Engine. The service authenticates Supabase users, stores documents (metadata + Supabase Storage), generates embeddings with FAISS, and calls Gemini for grounded responses.

## Features

- Supabase JWT validation and per-user enforcement
- Conversation CRUD (with cascading deletes of messages, documents, and vector store files)
- PDF ingestion, storage, and signed URL retrieval
- SentenceTransformer embeddings persisted to FAISS (per conversation)
- Gemini-based answer generation constrained to retrieved snippets

## Requirements

- Python 3.10 or newer
- Supabase project with a storage bucket for user uploads
- Google Generative AI (Gemini) API key

Install dependencies via `requirements.txt`:

```bash
python -m venv .venv
source .venv/bin/activate         # .\.venv\Scripts\activate on Windows
pip install --upgrade pip
pip install -r requirements.txt
```

## Environment Variables

Copy the sample file and edit it with your credentials:

```bash
cp .env.example .env
```

Required variables:

| Key | Description |
| --- | --- |
| `GOOGLE_API_KEY` | Gemini API key for `google-generativeai` |
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase service role key (for database/storage access) |
| `SUPABASE_BUCKET` | Supabase Storage bucket where PDFs are uploaded |
| `SUPABASE_JWT_SECRET` | JWT secret used to validate Supabase auth tokens |

Optional: adjust FAISS storage path in `services/vector_store.py`.

## Running the API

```bash
uvicorn backend.main:app --reload
```

The API listens on `http://127.0.0.1:8000` by default and exposes:

- `GET /` – health check
- `/conversations` – conversation CRUD
- `/conversations/{conversation_id}/messages` – chat history + Gemini answers
- `/conversations/{conversation_id}/documents` – PDF management + signed URLs

All routes expect:

- `Authorization: Bearer <Supabase access token>` header
- `user_id=<supabase-user-id>` query parameter (injected automatically by the frontend)

## Persistence Layout

- Supabase database tables: `conversations`, `messages`, `documents`
- Supabase Storage: `SUPABASE_BUCKET/<user_id>/<conversation_id>/<timestamp>_<filename>`
- Local FAISS index: `backend/db/vector_stores/{conversation_id}.pkl`

Deleting a conversation removes its documents (metadata + storage objects), FAISS index, and messages.

## Development Tips

- When embeddings or FAISS libraries change, delete the files under `backend/db/vector_stores/` to rebuild.
- For deterministic local testing, mock out Gemini responses in `services/llm_service.py`.
- Run the frontend alongside this API (`npm run dev` in `frontend/`) to exercise the full flow.

See the root `README.md` for overall project setup.
