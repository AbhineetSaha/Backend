# Backend – FastAPI Service

This directory contains the Retrieval-Augmented Generation (RAG) API that powers the Knowledge-Based Search Engine. The service authenticates Supabase users, stores documents (metadata + Supabase Storage), generates embeddings with FAISS, and uses local Hugging Face models for grounded responses.

## Features

- Supabase JWT validation and per-user enforcement
- Conversation CRUD (with cascading deletes of messages, documents, and vector store files)
- PDF ingestion, storage, and signed URL retrieval
- Sentence Transformer embeddings (default `sentence-transformers/all-MiniLM-L6-v2`) persisted to FAISS (per conversation)
- Hugging Face question-answering model (default `distilbert-base-cased-distilled-squad`) constrained to retrieved snippets

## Requirements

- Python 3.10 or newer
- Supabase project with a storage bucket for user uploads
- Ability to download Hugging Face models (defaults can run locally without API keys)

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
| `SUPABASE_URL` | Supabase project URL |
| `SUPABASE_KEY` | Supabase service role key (for database/storage access) |
| `SUPABASE_BUCKET` | Supabase Storage bucket where PDFs are uploaded |
| `SUPABASE_JWT_SECRET` | JWT secret used to validate Supabase auth tokens |

Optional overrides:

- Set `EMBEDDING_MODEL_NAME` to use a different Sentence Transformer for vector generation.
- Set `LLM_MODEL_NAME` (and optionally `LLM_MIN_CONFIDENCE`) to pick a different Hugging Face QA model.
- Adjust FAISS storage path with `VECTOR_STORE_DIR` (defaults to `db/vector_stores`).

## Running the API

```bash
uvicorn backend.main:app --reload
```

The API listens on `http://127.0.0.1:8000` by default and exposes:

- `GET /` – health check
- `/conversations` – conversation CRUD
- `/conversations/{conversation_id}/messages` – chat history + locally generated answers
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
- For deterministic local testing, mock out QA responses in `services/llm_service.py`.
- Run the frontend alongside this API (`npm run dev` in `frontend/`) to exercise the full flow.

See the root `README.md` for overall project setup.

## Deploying to Railway

This repo ships with `railway.json` and `nixpacks.toml` so Railway can detect the Python service and run it with `uvicorn` automatically. To deploy:

1. Install the Railway CLI and authenticate: `npm i -g @railway/cli && railway login`.
2. From this `Backend/` directory, create or link a service: `railway init` (choose an existing project or create a new one).
3. Push the code: `railway up`. Railway will use Nixpacks, install the dependencies in `requirements.txt`, and build a Python 3.11 image.
4. Set the required environment variables (`SUPABASE_URL`, `SUPABASE_KEY`, `SUPABASE_BUCKET`, `SUPABASE_JWT_SECRET`, optionally `CORS_ORIGINS`) via `railway variables set ...` or the Dashboard.
5. (Optional but recommended) Attach a persistent volume and set `VECTOR_STORE_DIR=/data/vector_stores` so FAISS indexes survive restarts. Without this, indexes are stored on the ephemeral filesystem.

After deploy, Railway exposes the API at the generated domain. The service responds to health checks on `/` and listens on the port that Railway injects through the `PORT` environment variable.
