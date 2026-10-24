import re
from typing import List


def split_text_into_chunks(text: str, max_chars: int = 2500) -> List[str]:
    """
    Splits text cleanly into chunks not exceeding max_chars.
    Respects sentence and paragraph boundaries (. ! ؟ \n).
    """
    text = (text or "").strip()
    if not text:
        return []

    if len(text) <= max_chars:
        return [text]

    chunks = []
    # Split by paragraphs first
    paragraphs = re.split(r'(\n+)', text)
    current_chunk = ""

    for part in paragraphs:
        if not part:
            continue
        # If adding this part exceeds max_chars
        if len(current_chunk) + len(part) > max_chars:
            if current_chunk.strip():
                chunks.append(current_chunk.strip())
                current_chunk = ""

            # If part itself is larger than max_chars, split by sentences
            if len(part) > max_chars:
                sentences = re.split(r'((?<=[.!?؛؟:])\s+)', part)
                for s in sentences:
                    if not s:
                        continue
                    if len(current_chunk) + len(s) > max_chars:
                        if current_chunk.strip():
                            chunks.append(current_chunk.strip())
                            current_chunk = ""
                        # If a single sentence exceeds max_chars, split on whitespace
                        if len(s) > max_chars:
                            words = s.split(' ')
                            for w in words:
                                if len(current_chunk) + len(w) + 1 > max_chars:
                                    if current_chunk.strip():
                                        chunks.append(current_chunk.strip())
                                        current_chunk = ""
                                current_chunk = (current_chunk + " " + w).strip()
                        else:
                            current_chunk = s
                    else:
                        current_chunk += s
            else:
                current_chunk = part
        else:
            current_chunk += part

    if current_chunk.strip():
        chunks.append(current_chunk.strip())

    return chunks
