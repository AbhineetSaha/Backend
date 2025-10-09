from db.supabase_client import supabase
from datetime import datetime

def save_message(conversation_id: str, sender: str, content: str):
    data = {"conversation_id": conversation_id, "sender": sender, "content": content, "timestamp": datetime.utcnow().isoformat()}
    supabase.table("messages").insert(data).execute()

def get_messages(conversation_id: str):
    res = supabase.table("messages").select("*").eq("conversation_id", conversation_id).order("timestamp").execute()
    return res.data

def delete_messages_for_conversation(conversation_id: str):
    supabase.table("messages").delete().eq("conversation_id", conversation_id).execute()
