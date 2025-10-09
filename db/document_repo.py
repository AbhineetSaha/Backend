import time
from db.supabase_client import supabase, SUPABASE_BUCKET

def _sanitize_name(filename: str) -> str:
    return (
        filename.replace(" ", "_")
        .replace("'", "")
        .replace('"', "")
        .replace(":", "_")
        .replace("/", "_")
    )

def upload_to_bucket(user_id: str, conversation_id: str, filename: str, file_bytes: bytes) -> str:
    safe_filename = _sanitize_name(filename)
    timestamp = int(time.time())
    path = f"{user_id}/{conversation_id}/{timestamp}_{safe_filename}"

    options = {
        "content-type": "application/pdf",
        "cache-control": "3600",
        "upsert": "true",  # strings only (http headers)
    }
    supabase.storage.from_(SUPABASE_BUCKET).upload(path, file_bytes, options)
    return path

def save_document(user_id: str, conversation_id: str, filename: str, path: str) -> str:
    res = supabase.table("documents").insert({
        "user_id": user_id,
        "conversation_id": conversation_id,
        "filename": filename,
        "storage_path": path,
        "include": True
    }).execute()
    return res.data[0]["id"]

def list_documents_for_conversation(conversation_id: str, user_id: str | None = None):
    query = supabase.table("documents").select("*").eq("conversation_id", conversation_id)
    if user_id is not None:
        query = query.eq("user_id", user_id)
    res = query.order("uploaded_at", desc=True).execute()
    return res.data

def get_document(doc_id: str):
    res = supabase.table("documents").select("*").eq("id", doc_id).single().execute()
    return res.data

def delete_document(doc_id: str):
    supabase.table("documents").delete().eq("id", doc_id).execute()

def set_document_inclusion(doc_id: str, include: bool):
    supabase.table("documents").update({"include": include}).eq("id", doc_id).execute()

def create_signed_url_for_path(path: str, expires_in: int = 60 * 10) -> str:
    # 10 minutes default
    res = supabase.storage.from_(SUPABASE_BUCKET).create_signed_url(path, expires_in)
    return res.get("signedURL") or res.get("signed_url") or res.get("data", {}).get("signedUrl")

def list_included_doc_ids(conversation_id: str) -> set[str]:
    res = supabase.table("documents").select("id, include").eq("conversation_id", conversation_id).execute()
    ids = set()
    for d in res.data or []:
        inc = d.get("include", True)
        # strict coercion: accept only True or "true"
        if isinstance(inc, bool):
            ok = inc
        elif isinstance(inc, str):
            ok = inc.strip().lower() == "true"
        else:
            ok = bool(inc)
        if ok:
            ids.add(d["id"])
    return ids

def delete_documents_for_conversation(conversation_id: str, user_id: str):
    res = (
        supabase.table("documents")
        .select("id, storage_path")
        .eq("conversation_id", conversation_id)
        .eq("user_id", user_id)
        .execute()
    )
    documents = res.data or []
    if documents:
        supabase.table("documents").delete().eq("conversation_id", conversation_id).eq("user_id", user_id).execute()
    return documents

def delete_paths_from_bucket(paths: list[str]):
    if not paths:
        return
    supabase.storage.from_(SUPABASE_BUCKET).remove(paths)
