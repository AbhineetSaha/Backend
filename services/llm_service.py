from functools import lru_cache
import os
from typing import Any, Dict

from dotenv import load_dotenv
from transformers import AutoModelForQuestionAnswering, AutoTokenizer, pipeline
from transformers.pipelines.base import Pipeline

load_dotenv()

_MODEL_NAME = os.getenv("LLM_MODEL_NAME", "distilbert-base-cased-distilled-squad")
_MIN_CONFIDENCE = float(os.getenv("LLM_MIN_CONFIDENCE", "0.2"))


@lru_cache(maxsize=1)
def _load_pipeline() -> Pipeline:
    """Initialise and cache the Hugging Face QA pipeline."""
    tokenizer = AutoTokenizer.from_pretrained(_MODEL_NAME)
    model = AutoModelForQuestionAnswering.from_pretrained(_MODEL_NAME)
    return pipeline("question-answering", model=model, tokenizer=tokenizer)


def _normalise_answer(response: Dict[str, Any]) -> str:
    answer = (response.get("answer") or "").strip()
    score = float(response.get("score") or 0.0)
    if not answer or score < _MIN_CONFIDENCE:
        return "I couldn’t find that in the document."
    return answer


def generate_answer(query: str, context: str) -> str:
    qa_pipeline = _load_pipeline()
    context = (context or "").strip()
    if not context:
        return "I couldn’t find that in the document."
    response = qa_pipeline(question=query, context=context)
    if isinstance(response, list):  # pipeline may return list for batched inputs
        response = response[0] if response else {}
    if not isinstance(response, dict):
        return "I couldn’t find that in the document."
    return _normalise_answer(response)
