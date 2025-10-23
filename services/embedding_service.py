import os
from functools import lru_cache
from typing import Iterable, List

from dotenv import load_dotenv
from fastembed import TextEmbedding

load_dotenv()

_EMBED_MODEL = os.getenv(
    "EMBEDDING_MODEL_NAME", "BAAI/bge-small-en-v1.5"
)


@lru_cache(maxsize=1)
def _load_model() -> TextEmbedding:
    """Load and cache the embedding model used for vector generation."""
    return TextEmbedding(model_name=_EMBED_MODEL)


def get_embeddings(texts: Iterable[str]) -> List[List[float]]:
    """Return embeddings for a batch of texts, skipping blanks."""
    clean_texts = [text.strip() for text in texts if text and text.strip()]
    if not clean_texts:
        return []
    model = _load_model()
    vectors = model.embed(clean_texts)
    return [vector.astype("float32").tolist() for vector in vectors]
