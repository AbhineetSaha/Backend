from fastapi import APIRouter, Depends, HTTPException, Query
from db.message_repo import get_messages, save_message
from db.document_repo import list_included_doc_ids
from services.auth_service import validate_user_token, enforce_user
from services.llm_service import generate_answer
from services.vector_store import VectorStore

router = APIRouter()

@router.get("/{conversation_id}/messages")
async def get_conversation_messages(
    conversation_id: str,
    user_id: str = Query(...),
    token_uid: str = Depends(validate_user_token),
    _: str = Depends(enforce_user),
):
    return get_messages(conversation_id)

@router.post("/{conversation_id}/messages")
async def send_message(
    conversation_id: str,
    body: dict,
    user_id: str = Query(...),
    token_uid: str = Depends(validate_user_token),
    _: str = Depends(enforce_user),
):
    question = (body or {}).get("content") or (body or {}).get("query")
    if not question:
        raise HTTPException(status_code=400, detail="Missing 'content' (or 'query') in body")

    # ✅ Get only truly-included doc IDs
    allowed_doc_ids = list_included_doc_ids(conversation_id)

    store = VectorStore(conversation_id)
    retrieved = store.search(question, top_k=8, restrict_doc_ids=allowed_doc_ids)
    context = "\n".join(retrieved)

    answer = generate_answer(question, context)
    save_message(conversation_id, "user", question)
    save_message(conversation_id, "ai", answer)
    return {"answer": answer}
