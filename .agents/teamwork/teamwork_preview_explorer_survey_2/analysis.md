# HexMedia Studio: LangGraph State, Conversation Memory & Titling Architecture Analysis

**Author:** Survey Explorer 2  
**Date:** 2026-10-24  
**Target System:** HexMedia Audio Drama Studio (`/root/hexmedia`)  
**Scope:** LangGraph Workflows, Checkpointer, ChatThread & Message Models, AI Titling, Soft Delete, Context Window Management  

---

## 1. Executive Summary

This investigation explores the current implementation and architectural gaps regarding LangGraph workflow state persistence, conversation session management, AI thread titling, soft deletion, and sliding-window context compression in HexMedia Studio.

### Core Discoveries:
1. **LangGraph State & Checkpointer**: Currently, `audio_drama_agent` (`backend/ai_studio/services/langgraph_controller.py:1281-1337`) is compiled without any checkpointer (`builder.compile()`). Invocations in `backend/ai_studio/api.py` (lines 130, 187, 259, 306) pass no `thread_id` or configuration. The state definition `AudioDramaState` lacks `thread_id`, `user_id`, and rolling `summary`. `psycopg` (v3.3.6) is connected to PostgreSQL on port 5439, and `langgraph-checkpoint-postgres` is installable without conflicts.
2. **Conversation Sessions & Data Structures**: No `ChatThread` model exists. Currently, generic chats overload `BookProject` with `status='CHAT'` (`langgraph_controller.py:641-652`), and `ChatMessage` points directly to `BookProject`. When visitors chat before project creation, messages have `project=None`, causing shared cross-visitor message pollution (`api.py:111`).
3. **Thread Titling**: Current titling is a naive string slice of the first user prompt (`clean_prompt[:35].rsplit(" ", 1)[0]` in `langgraph_controller.py:644`). There is no AI titling for general chat and no inline rename API.
4. **Soft Delete / Archival**: No soft delete flags (`is_deleted`, `deleted_at`) exist on any model. Deleting a scene performs a hard SQL `DELETE`. There is no thread deletion endpoint or archival state to keep assets visible in user profiles while removing them from the sidebar.
5. **Context Window Management**: `api.py:112` fetches a hardcoded slice of the last 8 messages (`[:8][::-1]`) with zero summarization. Older turns are silently discarded, losing character definitions, user directions, and story constraints.

---

## 2. Deep Dive: LangGraph Workflows & State Definitions

### 2.1 State Definition (`AudioDramaState`)
- **File**: `/root/hexmedia/backend/ai_studio/services/langgraph_controller.py` (Lines 22–37)
```python
class AudioDramaState(TypedDict):
    project_id: Optional[str]
    user_prompt: str
    file_content: Optional[str]
    filename: Optional[str]
    narration_mode: Optional[str]
    action: str  # 'chat', 'upload_book', 'approve_casting', 'execute_scene', 'execute_chapter'
    tool: Optional[str]
    chapter_number: Optional[int]
    history: List[Dict[str, str]]
    
    # Outputs
    response_text: str
    msg_type: str  # 'TEXT', 'CASTING_CARD', 'SCENE_AUDIO_CARDS', 'STUDIO_LINK'
    metadata: Dict[str, Any]
```

#### Identified Deficiencies:
- **Missing `thread_id`**: LangGraph checkpointers require a unique `thread_id` in `config={"configurable": {"thread_id": ...}}` to resume state.
- **Missing `user_id`**: Multi-tenancy isolation cannot be validated at the graph level without user identity.
- **Missing `summary`**: No field to pass accumulated conversation summary down into nodes.
- **Missing Intermediate State**: Workflow checkpoints for multi-step character casting or rendering recovery are not preserved across requests.

#### Proposed Enhanced State:
```python
class AudioDramaState(TypedDict):
    thread_id: str
    user_id: Optional[int]
    project_id: Optional[str]
    user_prompt: str
    file_content: Optional[str]
    filename: Optional[str]
    narration_mode: Optional[str]
    action: str
    tool: Optional[str]
    chapter_number: Optional[int]
    history: List[Dict[str, str]]
    summary: Optional[str]  # Rolling smart summary
    
    # Outputs
    response_text: str
    msg_type: str
    metadata: Dict[str, Any]
```

---

### 2.2 Graph Nodes & Execution Pipeline
- **File**: `/root/hexmedia/backend/ai_studio/services/langgraph_controller.py` (Lines 1280–1337)
- **Graph Topology**:
  - `router` (`router_node`, line 164): Pass-through entry point.
  - `route_action` (lines 1289–1318): Evaluates prompt keywords, `action`, `file_content`, and `project_id` to route to:
    - `book_ingestion` (lines 662–790): Parses documents via `analyze_book_text`, saves `BookProject`, `Character`, `Chapter` records, returns `CASTING_CARD`.
    - `execute_scene` (lines 792–1130): Chunks text into scenes, matches characters, synthesizes audio with Gemini TTS, matches SFX, builds DesignCombo JSON timeline.
    - `execute_chapter` (lines 1132–1278): Synthesizes audio for all scenes in a specific chapter.
    - `chat_agent` (`chat_node`, lines 167–660): Handles interactive chat, prompt authoring, duration adjustments, and fallback AI conversational response.
  - All worker nodes route directly to `END`.

---

### 2.3 Checkpointer Setup: PostgresSaver vs MemorySaver
- **Current State**:
  - `langgraph_controller.py:1335`: `return builder.compile()` without checkpointer.
  - Invocations in `backend/ai_studio/api.py`:
    - Line 130: `result = audio_drama_agent.invoke(state_input)`
    - Line 187: `result = audio_drama_agent.invoke(state_input)`
    - Line 259: `result = audio_drama_agent.invoke(state_input)`
    - Line 306: `result = audio_drama_agent.invoke(state_input)`
- **Evaluation**:
  1. `MemorySaver`:
     - Built into `langgraph.checkpoint.memory`.
     - Fast for in-process tests, but state is lost on process restart or across worker threads/processes.
  2. `PostgresSaver` (`langgraph-checkpoint-postgres`):
     - Official LangGraph checkpointer for PostgreSQL.
     - Connects via `psycopg_pool.ConnectionPool` using Django's database configuration (`postgresql://hexmedia_user:hexmedia_secret_password@127.0.0.1:5439/hexmedia`).
     - Calling `checkpointer.setup()` automatically provisions `checkpoints`, `checkpoint_blobs`, and `checkpoint_writes` tables in PostgreSQL.
  3. **Thread Keying Strategy**:
     - Keying by `f"user_{user.id}:thread_{thread.id}"` guarantees that LangGraph state is strictly partitioned per user and per conversation session, satisfying R1 and R3.
  4. **Fallback Design**:
     - Implement a checkpointer factory in `backend/ai_studio/services/checkpointer.py`:
       If PostgreSQL pool is active, return `PostgresSaver(pool)`; if running offline test fixtures without DB pool, gracefully fallback to `MemorySaver()`.

---

## 3. Deep Dive: ChatThread & Message Data Structures, Conversation Management

### 3.1 Current Models & Shortcomings
- **File**: `/root/hexmedia/backend/ai_studio/models.py`
  - `BookProject` (lines 51–112): Contains fields for title, author, genre, `status` (including `'CHAT'`), duration, narration mode, visual style.
  - `ChatMessage` (lines 252–281):
    ```python
    class ChatMessage(models.Model):
        id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
        project = models.ForeignKey(BookProject, on_delete=models.CASCADE, null=True, blank=True, related_name='messages')
        role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='ASSISTANT')
        content = models.TextField()
        msg_type = models.CharField(max_length=30, choices=MSG_TYPE_CHOICES, default='TEXT')
        metadata = models.JSONField(default=dict, blank=True)
        created_at = models.DateTimeField(auto_now_add=True)
    ```
- **Architectural Gaps**:
  1. Conflation of "Chat Session" with "Book Project": General chat creates a dummy `BookProject(title=..., status='CHAT')` (`langgraph_controller.py:647`).
  2. Inability to isolate conversations: No `user` ForeignKey on `BookProject` or `ChatMessage`.
  3. Leaking context for anonymous/unassigned messages: When `project=None`, `qs = ChatMessage.objects.filter(project__isnull=True)` pools all unassigned messages together (`api.py:111`).
  4. No relationship representing the thread as master container for novel generation, character casting, and media assets.

### 3.2 Proposed `ChatThread` Data Model
```python
class ChatThread(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='threads')
    title = models.CharField(max_length=255, default="محادثة جديدة")
    project = models.ForeignKey(BookProject, on_delete=models.SET_NULL, null=True, blank=True, related_name='threads')
    summary = models.TextField(blank=True, default="", help_text="الملخص التراكمي للمحادثة السابقة")
    is_deleted = models.BooleanField(default=False, db_index=True)
    deleted_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "محادثة (Chat Thread)"
        verbose_name_plural = "سجل المحادثات (Chat Threads)"
        ordering = ['-updated_at']

    def __str__(self):
        return f"[{self.user.username}] {self.title}"
```

### 3.3 Enhanced `ChatMessage` Model
```python
class ChatMessage(models.Model):
    ...
    thread = models.ForeignKey(ChatThread, on_delete=models.CASCADE, related_name='messages', null=True, blank=True)
    project = models.ForeignKey(BookProject, on_delete=models.CASCADE, null=True, blank=True, related_name='messages')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, null=True, blank=True, related_name='chat_messages')
    ...
```

### 3.4 Conversation Session Lifecycle
1. **Creation**:
   - Starting a new chat generates a `ChatThread(user=user, title="محادثة جديدة")`.
   - In visitor onboarding mode: visitor prompt is saved in localStorage, and upon login/register, the thread is created with that prompt as its initial message.
2. **Execution**:
   - `POST /api/chat` accepts `thread_id: Optional[str]`. If omitted, automatically creates a new `ChatThread`.
   - User message is stored in `ChatMessage(thread=thread, user=user, role='USER', content=prompt)`.
   - When a story or audio drama is authored, `thread.project` points to the new `BookProject`.
3. **Switching & Retrieval**:
   - `GET /api/threads`: Returns user's active threads grouped by recency (Today, Yesterday, Previous 7 Days).
   - `GET /api/threads/{thread_id}/messages`: Returns full message history and attached project details without page reload.

---

## 4. Deep Dive: Automatic AI Thread Titling

### 4.1 Current Implementation Point
- **File**: `/root/hexmedia/backend/ai_studio/services/langgraph_controller.py` (Lines 643–647)
```python
clean_prompt = prompt.strip().replace("\n", " ")
short_title = clean_prompt[:35].rsplit(" ", 1)[0] if len(clean_prompt) > 35 else clean_prompt
if not short_title:
    short_title = "محادثة جديدة"
```
- **Observations**:
  - This is a crude character truncation, not AI titling.
  - Result: Titles like "اكتب لي سيناريو عن رحلة في" or "ممكن تساعدني في كتابة".
  - Fails acceptance criteria: "Submitting the first message in a new session automatically generates and assigns a title to the thread."

### 4.2 Proposed AI Titling Implementation
- **Location**: In `backend/ai_studio/services/gemini_service.py`:
```python
def generate_thread_title(prompt: str, response: str = "") -> str:
    """Generates a concise 3-5 word title for a conversation thread using Gemini Flash."""
    client, config = get_gemini_client()
    if not client:
        words = [w for w in re.sub(r'[^\w\s]', '', prompt).split() if len(w) > 2]
        filtered = [w for w in words if w not in ["اكتب", "أريد", "ممكن", "اعمل", "سوي", "توليد", "ألف"]]
        return " ".join(filtered[:4]) or "محادثة جديدة"

    try:
        system_instruction = (
            "أنت محرر سينمائي وصحفي موجز. "
            "مهمتك صياغة عنوان جذاب وموجز جداً (من 3 إلى 5 كلمات فقط) "
            "يعبر بدقة عن الفكرة الجوهرية أو قصة المحادثة. "
            "اكتب العنوان مباشرة فقط باللغة العربية بدون علامات تنصيص أو شروحات."
        )
        user_content = f"رسالة المستخدم الأولى:\n{prompt[:300]}\n\nمقتطف الرد:\n{response[:300]}"
        res = client.models.generate_content(
            model=config.llm_model or "gemini-3.8-flash",
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.4,
                max_output_tokens=30,
            )
        )
        title = res.text.strip().strip('"\'').split('\n')[0].strip()
        return title[:60] if title else "محادثة جديدة"
    except Exception as e:
        logger.error(f"Error generating thread title: {e}")
        return "محادثة جديدة"
```

### 4.3 Trigger Flow in `chat_endpoint`
1. Before or during assistant response generation, inspect `thread.messages.filter(role='USER').count()`.
2. If count == 1 (first user turn) or `thread.title == "محادثة جديدة"`:
   - Call `new_title = generate_thread_title(prompt, assistant_text)`
   - Save `thread.title = new_title; thread.save(update_fields=['title'])`
   - Inject `"thread_title": new_title` into `ChatResponse.metadata`.
3. Provide manual rename API:
   - `PATCH /api/threads/{thread_id}` with `{ "title": "..." }`. Validates ownership and updates the database.

---

## 5. Deep Dive: Soft Delete & Archival Mechanism

### 5.1 Current Implementation State
- No soft delete support anywhere in the backend.
- Deletions in `api.py` line 551 (`delete_scene_endpoint`) run hard SQL deletes (`scene.delete()`).
- No endpoint exists to delete or archive chat threads or projects.
- `views.py:14`: `BookProject.objects.all().order_by('-created_at')[:15]` displays all projects indiscriminately.

### 5.2 Archival Data Preservation Architecture
- **Separation of Concerns**:
  - Deleting a conversation thread from the sidebar must **NOT** destroy the creative deliverables created during that conversation (audio master tracks, video renders, chapters, scenes, characters).
  - Marking `ChatThread.is_deleted = True` and recording `ChatThread.deleted_at = timezone.now()` removes the thread from the active chat sidebar.
  - The linked `BookProject` remains fully intact in PostgreSQL and MinIO.
  - The User Profile "My Projects & Media" library queries all `BookProject.objects.filter(user=request.user)`, allowing users to browse, play, and download past creative works even after deleting the chat thread from their sidebar.
- **Required Endpoints**:
  - `DELETE /api/threads/{thread_id}`: Sets `is_deleted = True`. Returns 200 OK.
  - `POST /api/threads/{thread_id}/restore`: Sets `is_deleted = False, deleted_at = None`.
  - `GET /api/user/media`: Lists all audio drama projects, master audio URLs, video renders, and script transcripts owned by the user.

---

## 6. Deep Dive: Context Window Management (Sliding Window + Rolling Summary)

### 6.1 Current Implementation & Flaws
- **File**: `/root/hexmedia/backend/ai_studio/api.py` (Lines 110–114)
```python
# Fetch last 8 messages for context
history_msgs = []
qs = ChatMessage.objects.filter(project=project) if project else ChatMessage.objects.filter(project__isnull=True)
for m in qs.order_by('-created_at')[:8][::-1]:
    history_msgs.append({"role": m.role, "content": m.content})
```
- **Flaws**:
  1. Truncates all dialogue turns prior to the last 8 messages.
  2. No memory of decisions made in turns 1–4 once conversation reaches turn 9.
  3. No token-size bounding: 8 large novel chapters will overflow the model context or inflate latency, while short messages waste available window.
  4. Disconnected from multi-turn LangGraph agent workflows.

### 6.2 Proposed Sliding Window + Rolling Summary Engine
- **Specifications**:
  - Let $N = 6$ messages (3 complete turns: User + Assistant) be the active sliding window.
  - Maximum summary length: 1,500 characters (~300 tokens).
  - Total prompt payload remains strictly bounded regardless of conversation length (e.g. 50 turns).

#### Algorithm:
```
1. Fetch all messages for thread in chronological order:
   all_msgs = thread.messages.order_by('created_at')

2. If len(all_msgs) <= N:
   active_window = all_msgs
   effective_summary = thread.summary

3. Else (len(all_msgs) > N):
   active_window = all_msgs[-N:]
   evicted_msgs = all_msgs[:-N]
   
   # If there are evicted messages not yet reflected in thread.summary:
   # Compute delta and call update_rolling_summary(thread.summary, delta_messages)
   thread.summary = update_rolling_summary(thread.summary, new_evicted)
   thread.save(update_fields=['summary'])
   effective_summary = thread.summary

4. Inject effective_summary into LangGraph AudioDramaState and Gemini system instruction:
   system_instruction += f"\n\n[ملخص المحادثة وسياق الأحداث السابقة]:\n{effective_summary}"
```

#### Rolling Summary Generator:
- **Location**: `backend/ai_studio/services/gemini_service.py`
```python
def update_rolling_summary(current_summary: str, evicted_messages: list) -> str:
    """Compresses newly evicted conversation turns into the rolling summary."""
    client, config = get_gemini_client()
    if not client:
        additions = "\n".join([f"{m.role}: {m.content[:80]}" for m in evicted_messages])
        return (current_summary + "\n" + additions)[-1500:]

    system_instruction = (
        "أنت خبير في تلخيص وضغط سياق المحادثات الطويلة للذكاء الاصطناعي. "
        "لديك ملخص سابق للمحادثة، وقائمة برسائل جديدة خرجت من نافذة السياق المباشر. "
        "قم بتحديث الملخص ليدمج الأحداث والقرارات والشخصيات والتعليمات الجديدة "
        "مع الحفاظ على إيجاز شديد ودقة عالية (بحد أقصى 200 كلمة). "
        "اكتب الملخص كفقرة واحدة متماسكة باللغة العربية."
    )
    evicted_text = "\n".join([f"- {m.role}: {m.content}" for m in evicted_messages])
    user_prompt = f"الملخص السابق:\n{current_summary or 'لا يوجد ملخص سابق.'}\n\nالرسائل المراد إضافتها:\n{evicted_text}"

    try:
        res = client.models.generate_content(
            model=config.llm_model or "gemini-3.8-flash",
            contents=user_prompt,
            config=types.GenerateContentConfig(
                system_instruction=system_instruction,
                temperature=0.3,
                max_output_tokens=300
            )
        )
        return res.text.strip()[:1500]
    except Exception as e:
        logger.error(f"Error updating rolling summary: {e}")
        return current_summary
```

---

## 7. Actionable Implementation Blueprint for Subsequent Work

| Component | Target File | Actions Required |
|---|---|---|
| **Models** | `backend/ai_studio/models.py` | Add `ChatThread` model with `user`, `title`, `project`, `summary`, `is_deleted`, `deleted_at`. Add `thread` and `user` FK to `ChatMessage`. Add `user` FK to `BookProject`. |
| **Checkpointer** | `backend/ai_studio/services/checkpointer.py` | Configure `PostgresSaver` via `psycopg_pool.ConnectionPool` pointing to Django PostgreSQL DB; provide `MemorySaver` fallback for tests. |
| **LangGraph Agent** | `backend/ai_studio/services/langgraph_controller.py` | Update `AudioDramaState` with `thread_id`, `user_id`, `summary`. Compile graph with `checkpointer`. Update `chat_node` to consume rolling summary. |
| **API Endpoints** | `backend/ai_studio/api.py` | Add `GET /api/threads`, `POST /api/threads`, `PATCH /api/threads/{id}`, `DELETE /api/threads/{id}`. Update `POST /api/chat` to enforce user isolation, thread keying, sliding window + rolling summary, and automatic AI titling. |
| **Titling & Summary** | `backend/ai_studio/services/gemini_service.py` | Add `generate_thread_title` (3-5 words) and `update_rolling_summary`. |
| **Test Verification** | `backend/ai_studio/tests.py` | Add test cases for thread lifecycle, multi-tenant isolation, sliding window bounding, and checkpointer turn recovery. Verify with `./init.sh`. |
