import os
import pickle
from typing import Iterable, List, Optional, Set, Tuple

import faiss
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
        self.index: Optional[faiss.IndexFlatL2] = None
        self.docs: List[Tuple[str, Optional[str]]] = []  # list of (text, doc_id)
        self._load()

    def _load(self):
        if os.path.exists(self.path):
            with open(self.path, "rb") as f:
                index, docs = pickle.load(f)
            self.index = index
            self.docs = [
                entry if isinstance(entry, tuple) and len(entry) == 2 else (entry, None)
                for entry in docs or []
            ]

    def _persist(self):
        with open(self.path, "wb") as f:
            pickle.dump((self.index, self.docs), f)

    def add(self, texts: Iterable[str], doc_id: str):
        texts = _clean_texts(texts)
        if not texts:
            return
        vectors = _embed(texts)
        if vectors.size == 0:
            return
        if self.index is None:
            self.index = faiss.IndexFlatL2(vectors.shape[1])
        self.index.add(vectors)
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
        self.index = faiss.IndexFlatL2(vectors.shape[1])
        self.index.add(vectors)
        self.docs = kept_entries
        self._persist()

    def search(self, query: str, top_k: int = 8, restrict_doc_ids: Optional[Set[str]] = None) -> List[str]:
        if self.index is None or not self.docs:
            return []
        q_vec = _embed([query])
        if q_vec.size == 0:
            return []
        _, I = self.index.search(q_vec, top_k * 3)  # overfetch
        results: List[str] = []
        for idx in I[0]:
            if idx < 0 or idx >= len(self.docs):
                continue
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
        self.index = None
        self.docs = []
