from fastapi import HTTPException
from uuid import UUID

def ensure_uuid(value: str, name: str = "id") -> str:
    try:
        UUID(value)
        return value
    except Exception:
        raise HTTPException(status_code=400, detail=f"Invalid {name}: expected UUID")
