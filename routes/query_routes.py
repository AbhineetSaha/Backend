from fastapi import APIRouter, Depends
from services.auth_service import validate_user_token
from services.vector_store import VectorStore
from services.llm_service import generate_answer
from db.message_repo import save_message

router = APIRouter()

@router.post("/{conversation_id}")
async def query(conversation_id: str, body: dict, user_id: str = Depends(validate_user_token)):
    """Query the uploaded documents with Gemini RAG"""
    question = body.get("query")
    store = VectorStore(conversation_id)
    retrieved_chunks = store.search(question, top_k=5)
    context = "\n".join(retrieved_chunks)

    answer = generate_answer(question, context)
    save_message(conversation_id, "user", question)
    save_message(conversation_id, "ai", answer)

    return {"answer": answer}
