"""
HexMedia Models Facade
Re-exports modular models from core, book_drama, and image_video for complete backward compatibility.
"""
from core.models import AIConfiguration, ChatThread, ChatMessage
from book_drama.models import BookProject, Character, Chapter
from image_video.models import Scene, TimelineState

__all__ = [
    'AIConfiguration',
    'BookProject',
    'Character',
    'Chapter',
    'Scene',
    'TimelineState',
    'ChatThread',
    'ChatMessage',
]
