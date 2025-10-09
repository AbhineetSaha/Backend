from datetime import datetime

from db.supabase_client import supabase


def create_conversation(user_id: str, title: str = "New Conversation"):
    data = {
        "user_id": user_id,
        "title": title,
        "updated_at": datetime.utcnow().isoformat(),
    }
    res = supabase.table("conversations").insert(data).execute()
    return res.data[0]["id"]


def get_user_conversations(user_id: str):
    res = (
        supabase.table("conversations")
        .select("*")
        .eq("user_id", user_id)
        .order("updated_at", desc=True)
        .execute()
    )
    return res.data


def update_conversation_title(conversation_id: str, user_id: str, title: str):
    """Rename a conversation and refresh its updated_at timestamp."""
    data = {"title": title, "updated_at": datetime.utcnow().isoformat()}
    supabase.table("conversations").update(data).eq("id", conversation_id).eq(
        "user_id", user_id
    ).execute()


def delete_conversation(conversation_id: str, user_id: str):
    # RLS should protect; we also scope by user in case RLS isn't on
    supabase.table("conversations").delete().eq("id", conversation_id).eq(
        "user_id", user_id
    ).execute()
