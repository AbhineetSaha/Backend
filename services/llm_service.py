import os
import re
from typing import List, Sequence, Tuple

from dotenv import load_dotenv
import numpy as np

from services.embedding_service import get_embeddings

load_dotenv()

_MIN_CONFIDENCE = float(os.getenv("LLM_MIN_CONFIDENCE", "0.2"))
_MAX_SENTENCES = int(os.getenv("LLM_MAX_SENTENCES", "2"))


def _split_context(context: str) -> List[str]:
    sentences = [
        sentence.strip()
        for sentence in re.split(r"(?<=[.!?])\s+", context)
        if sentence and sentence.strip()
    ]
    if not sentences:
        stripped = context.strip()
        return [stripped] if stripped else []
    return sentences


def _similarity_scores(query: str, sentences: Sequence[str]) -> List[Tuple[float, str]]:
    if not sentences:
        return []
    embeddings = get_embeddings([query, *sentences])
    if len(embeddings) <= 1:
        return []
    vectors = np.array(embeddings, dtype="float32")
    query_vec = vectors[0]
    sentence_vecs = vectors[1:]
    query_norm = query_vec / (np.linalg.norm(query_vec) + 1e-12)
    sentence_norms = sentence_vecs / np.maximum(
        np.linalg.norm(sentence_vecs, axis=1, keepdims=True), 1e-12
    )
    scores = sentence_norms @ query_norm
    return list(zip(scores.tolist(), sentences))


def generate_answer(query: str, context: str) -> str:
    context = (context or "").strip()
    if not context:
        return "I couldn’t find that in the document."
    sentences = _split_context(context)
    scored = sorted(
        _similarity_scores(query, sentences), key=lambda item: item[0], reverse=True
    )
    if not scored:
        return "I couldn’t find that in the document."
    confident = [text for score, text in scored if score >= _MIN_CONFIDENCE]
    top_candidates = confident or [scored[0][1]]
    answer = " ".join(top_candidates[: max(_MAX_SENTENCES, 1)])
    return answer.strip() or "I couldn’t find that in the document."
