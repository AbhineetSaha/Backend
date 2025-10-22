import os
from functools import lru_cache
from typing import Iterable, List

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

_EMBED_MODEL = os.getenv(
    "EMBEDDING_MODEL_NAME", "sentence-transformers/all-MiniLM-L6-v2"
)


@lru_cache(maxsize=1)
def _load_model() -> SentenceTransformer:
    """Load and cache the sentence transformer used for embeddings."""
    return SentenceTransformer(_EMBED_MODEL)


def get_embeddings(texts: Iterable[str]) -> List[List[float]]:
    """Return embeddings for a batch of texts, skipping blanks."""
    clean_texts = [text.strip() for text in texts if text and text.strip()]
    if not clean_texts:
        return []
    model = _load_model()
    vectors = model.encode(clean_texts, convert_to_numpy=True, show_progress_bar=False)
    return [vector.astype("float32").tolist() for vector in vectors]
