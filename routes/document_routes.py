from fastapi import APIRouter, UploadFile, Depends, HTTPException, Query
from io import BytesIO
from ._validators import ensure_uuid
from services.auth_service import validate_user_token, enforce_user
from utils.pdf_loader import load_pdf
from services.vector_store import VectorStore
from db.document_repo import (
    upload_to_bucket,
    save_document,
    list_documents_for_conversation,
    delete_document,
    set_document_inclusion,
    get_document,
    create_signed_url_for_path,
)

router = APIRouter()

@router.get("/{conversation_id}/documents")
async def list_documents(
    conversation_id: str,
    user_id: str = Query(...),
    token_uid: str = Depends(validate_user_token),
    _: str = Depends(enforce_user),
):
    ensure_uuid(conversation_id, "conversation_id")
    return list_documents_for_conversation(conversation_id, user_id)

@router.post("/{conversation_id}/documents")
async def upload_document(
    conversation_id: str,
    file: UploadFile,
    user_id: str = Query(...),
    token_uid: str = Depends(validate_user_token),
    _: str = Depends(enforce_user),
):
    ensure_uuid(conversation_id, "conversation_id")
    bytes_ = await file.read()

    # Upload to Supabase Storage
    path = upload_to_bucket(user_id, conversation_id, file.filename, bytes_)

    # Create document record (returns doc_id)
    doc_id = save_document(user_id, conversation_id, file.filename, path)

    # Parse and embed per-doc chunks with doc_id
    text = load_pdf(BytesIO(bytes_))
    chunks = [text[i:i+500] for i in range(0, len(text), 500)] if text else []
    if chunks:
        store = VectorStore(conversation_id)
        store.add(chunks, doc_id=doc_id)

    return {"status": "uploaded", "chunks": len(chunks), "path": path, "doc_id": doc_id}

@router.delete("/{conversation_id}/documents/{doc_id}")
async def remove_document(
    conversation_id: str,
    doc_id: str,
    user_id: str = Query(...),
    token_uid: str = Depends(validate_user_token),
    _: str = Depends(enforce_user),
):
    ensure_uuid(conversation_id, "conversation_id")
    # Remove from vector index (all chunks for this doc)
    store = VectorStore(conversation_id)
    store.remove_doc(doc_id)

    # Remove record (does not delete storage file; keep or extend if needed)
    delete_document(doc_id)
    return {"ok": True}

@router.patch("/{conversation_id}/documents/{doc_id}")
async def toggle_document_inclusion(
    conversation_id: str,
    doc_id: str,
    body: dict,
    user_id: str = Query(...),
    token_uid: str = Depends(validate_user_token),
    _: str = Depends(enforce_user),
):
    ensure_uuid(conversation_id, "conversation_id")
    # Body: { include: boolean }
    include = (body or {}).get("include")
    if include is None:
        raise HTTPException(status_code=400, detail="Missing 'include' boolean in body")
    set_document_inclusion(doc_id, include)
    return {"ok": True, "doc_id": doc_id, "include": include}

@router.get("/{conversation_id}/documents/{doc_id}/url")
async def get_document_url(
    conversation_id: str,
    doc_id: str,
    user_id: str = Query(...),
    token_uid: str = Depends(validate_user_token),
    _: str = Depends(enforce_user),
):
    ensure_uuid(conversation_id, "conversation_id")
    doc = get_document(doc_id)
    if not doc or doc["conversation_id"] != conversation_id:
        raise HTTPException(status_code=404, detail="Document not found")
    url = create_signed_url_for_path(doc["storage_path"])
    return {"url": url}
