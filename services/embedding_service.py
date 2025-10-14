import os
from typing import Iterable, List

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()
_API_KEY = os.getenv("GOOGLE_API_KEY")
if not _API_KEY:
    raise RuntimeError("GOOGLE_API_KEY must be set to request embeddings from Gemini.")
genai.configure(api_key=_API_KEY)

_EMBED_MODEL = os.getenv("GOOGLE_EMBED_MODEL", "models/text-embedding-004")


def _embed_text(text: str) -> List[float]:
    """Request a single embedding vector from Google Generative AI."""
    response = genai.embed_content(
        model=_EMBED_MODEL,
        content=text,
        task_type="retrieval_document",
    )
    embedding = response.get("embedding")
    if embedding is None:
        raise RuntimeError("Google Generative AI returned no embedding data.")
    return embedding


def get_embeddings(texts: Iterable[str]) -> List[List[float]]:
    """Return embeddings for a batch of texts, skipping blanks."""
    clean_texts = [text.strip() for text in texts if text and text.strip()]
    if not clean_texts:
        return []
    return [_embed_text(text) for text in clean_texts]
