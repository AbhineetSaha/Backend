from fastapi import APIRouter, Depends, Query
from services.auth_service import validate_user_token, enforce_user
from services.vector_store import VectorStore
from db.conversation_repo import (
    create_conversation,
    delete_conversation,
    get_user_conversations,
    update_conversation_title,
)
from db.document_repo import (
    delete_documents_for_conversation,
    delete_paths_from_bucket,
)
from db.message_repo import delete_messages_for_conversation
from models.schemas import ConversationCreate, ConversationUpdate
from ._validators import ensure_uuid

router = APIRouter()

@router.get("")
async def list_conversations(
    user_id: str = Query(...),
    token_uid: str = Depends(validate_user_token),
    _: str = Depends(enforce_user),
):
    return get_user_conversations(user_id)

@router.post("")
async def new_conversation(
    payload: ConversationCreate,
    user_id: str = Query(...),
    token_uid: str = Depends(validate_user_token),
    _: str = Depends(enforce_user),
):
    conv_id = create_conversation(user_id, payload.title or "New Conversation")
    return {"conversation_id": conv_id}

@router.delete("/{conversation_id}")
async def remove_conversation(
    conversation_id: str,
    user_id: str = Query(...),
    token_uid: str = Depends(validate_user_token),
    _: str = Depends(enforce_user),
):
    ensure_uuid(conversation_id, "conversation_id")
    documents = delete_documents_for_conversation(conversation_id, user_id)
    if documents:
        storage_paths = [
            doc["storage_path"] for doc in documents if doc.get("storage_path")
        ]
        delete_paths_from_bucket(storage_paths)
    VectorStore(conversation_id).delete_store()
    delete_messages_for_conversation(conversation_id)
    delete_conversation(conversation_id, user_id)
    return {"ok": True}


@router.patch("/{conversation_id}")
async def rename_conversation(
    conversation_id: str,
    payload: ConversationUpdate,
    user_id: str = Query(...),
    token_uid: str = Depends(validate_user_token),
    _: str = Depends(enforce_user),
):
    ensure_uuid(conversation_id, "conversation_id")
    update_conversation_title(conversation_id, user_id, payload.title)
    return {"ok": True}
