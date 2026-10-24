"""Core memory & history helpers."""
from typing import List, Dict, Any
from ..models import ChatThread

MEMORY_WINDOW = 20

def build_history_window(thread: ChatThread, limit: int = MEMORY_WINDOW) -> List[Dict[str, Any]]:
    """Return the last `limit` messages of a thread as role/content dicts."""
    if not thread:
        return []
    msgs = thread.messages.order_by('-created_at')[:limit]
    history = []
    for m in reversed(list(msgs)):
        history.append({
            "role": m.role.lower(),
            "content": m.content
        })
    return history
