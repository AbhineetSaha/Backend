import os
import pickle
from typing import Iterable, List, Optional, Sequence, Set, Tuple

import numpy as np

from services.embedding_service import get_embeddings

STORE_DIR = os.getenv("VECTOR_STORE_DIR", "db/vector_stores")
os.makedirs(STORE_DIR, exist_ok=True)


def _clean_texts(texts: Iterable[str]) -> List[str]:
    return [text.strip() for text in texts if text and text.strip()]


def _embed(texts: Iterable[str]) -> np.ndarray:
    vectors = get_embeddings(texts)
    if not vectors:
        return np.array([], dtype="float32")
    return np.array(vectors, dtype="float32")


# Stored payload: (index, [(text, doc_id)])
class VectorStore:
    def __init__(self, conv_id: str):
        self.conv_id = conv_id
        self.path = os.path.join(STORE_DIR, f"{conv_id}.pkl")
        self.vectors: Optional[np.ndarray] = None
        self.docs: List[Tuple[str, Optional[str]]] = []  # list of (text, doc_id)
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "rb") as f:
                vectors, docs = pickle.load(f)
            self.vectors = vectors
            self.docs = [
                entry if isinstance(entry, tuple) and len(entry) == 2 else (entry, None)
                for entry in docs or []
            ]

    def _persist(self):
        with open(self.path, "wb") as f:
            pickle.dump((self.vectors, self.docs), f)

    def add(self, texts: Iterable[str], doc_id: str):
        texts = _clean_texts(texts)
        if not texts:
            return
        vectors = _embed(texts)
        if vectors.size == 0:
            return
        if self.vectors is None:
            self.vectors = vectors
        else:
            self.vectors = np.vstack([self.vectors, vectors])
        self.docs.extend([(text, doc_id) for text in texts])
        self._persist()

    def remove_doc(self, doc_id: str):
        if not self.docs:
            return
        kept_entries = [(text, d_id) for text, d_id in self.docs if d_id != doc_id]
        if len(kept_entries) == len(self.docs):
            return  # Nothing to remove
        if not kept_entries:
            self.delete_store()
            return
        vectors = _embed([text for text, _ in kept_entries])
        if vectors.size == 0:
            self.delete_store()
            return
        self.vectors = vectors
        self.docs = kept_entries
        self._persist()

    def search(self, query: str, top_k: int = 8, restrict_doc_ids: Optional[Set[str]] = None) -> List[str]:
        if self.vectors is None or not self.docs:
            return []
        q_vec = _embed([query])
        if q_vec.size == 0:
            return []
        candidates = _top_k_cosine(self.vectors, q_vec[0], top_k * 3)
        results: List[str] = []
        for idx in candidates:
            text, d_id = self.docs[idx]
            if restrict_doc_ids is not None and (not d_id or d_id not in restrict_doc_ids):
                continue
            results.append(text)
            if len(results) >= top_k:
                break
        return results

    def delete_store(self):
        """Remove the persisted vector store for this conversation."""
        if os.path.exists(self.path):
            os.remove(self.path)
        self.vectors = None
        self.docs = []


def _top_k_cosine(matrix: np.ndarray, query: np.ndarray, k: int) -> Sequence[int]:
    if matrix.size == 0:
        return []
    k = max(k, 1)
    matrix_norms = np.linalg.norm(matrix, axis=1, keepdims=True)
    matrix_norm = matrix / np.maximum(matrix_norms, 1e-12)
    query_norm = query / (np.linalg.norm(query) + 1e-12)
    scores = matrix_norm @ query_norm
    top_k_idx = np.argsort(-scores)[: min(k, matrix.shape[0])]
    return top_k_idx.tolist()
