# HexMedia Studio — Session Progress

## Session 3 — 2026-10-24

### Completed ✅

**M1 — Auth & Data Isolation** (prev session)
- Hybrid JWT + Django Session auth
- `/api/auth/register|login|logout|refresh|me`
- User FK on BookProject + ChatMessage (migration 0007)
- 46 tests passing

**M2 — Chat Thread Memory**
- `ChatThread` model: UUID PK, user FK, soft-delete, auto-title
- `ChatMessage.thread` FK (migration 0008)
- CRUD: `GET/POST /api/threads`, `GET /api/threads/{id}`, `GET /api/threads/{id}/messages`
- `PATCH /api/threads/{id}/rename`, `DELETE /api/threads/{id}` (soft)
- Sliding window memory: `_build_history(thread, limit=20)` 
- `chat_endpoint` wired: resume thread via `thread_id` or auto-create with AI title

**M3 — Sidebar UI & Auth Modals** (partially by subagent before quota)
- `loginModal` + `registerModal` in index.html
- `pendingPrompt` visitor onboarding flow
- `loadUserThreads()` + `switchThread()` JS functions
- Thread list grouped by Today/Yesterday/Last 7 Days
- Ctrl+K new chat, Ctrl+B sidebar toggle

### Evidence
- 46/46 Django tests pass (`python backend/manage.py test ai_studio.tests --keepdb`)
- Smoke tests: create thread → send chat → auto-title → rename → soft-delete ✅
- API import clean, migration 0008 applied
- Git commit: bbc9d8c

### Session 5 — 2026-10-24: Fix Real Gemini 3.5 Transcribe & Subtitles

### Completed ✅
- **Root Cause Diagnosed**:
  - `gemini-3.5-transcribe` is a dedicated STT model that outputs `audio_transcription` object parts (`speaker_label`, `words`, `start_offset`, `end_offset`, `text`), NOT a JSON string.
  - Previous code attempted `json.loads(response.text)` on pure text, throwing `JSONDecodeError` and silently falling back to the static hardcoded Arabic sentence.
- **Implemented Real Gemini Integration**:
  - Configured `AudioTranscriptionConfig(language_codes=..., diarization=..., word_timestamp=True)`.
  - Extracted exact spoken words, timestamps, and speaker labels (`متحدث 1`, `متحدث 2`) from `part.audio_transcription`.
  - Added multi-language translation support via `gemini-3.8-flash` preserving segment timing and speakers.
  - Tested live on user's recording: accurately transcribed `"السلام عليكم ورحمة الله وبركاته، ايه الاخبار؟"` and translated to Russian `"Мир вам, милость Аллаха и Его благословение, как дела?"`.
  - All 11 STT unit tests pass in `backend/stt/tests_stt.py`.

---

## Session 4 — 2026-10-24: Traefik HTTPS Deployment (nip.io)

### Completed ✅
- **Traefik Dynamic Routing**:
  - Added `hexmedia-http` (HTTP:80 -> HTTPS:443 308 redirect) and `hexmedia-https` (HTTPS:443 with `myresolver` ACME Let's Encrypt SSL) to `/root/motaem/traefik_data/voice_dynamic.yml`.
  - Added `hexmedia-minio-http` and `hexmedia-minio-https` for SSL asset streaming (`hexmedia-assets.169.58.32.179.nip.io`).
  - Added `hexmedia-redirect-https` middleware.
  - Zero downtime / zero interference with other live systems (`uggu.space`, telephony/voice services).
- **Django Proxy & Security Settings**:
  - `SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')`
  - `USE_X_FORWARDED_HOST = True`
  - `USE_X_FORWARDED_PORT = True`
  - `ALLOWED_HOSTS` updated with nip.io domains.
  - `CSRF_TRUSTED_ORIGINS` updated with `https://hexmedia.169.58.32.179.nip.io`, `https://hexmedia-assets.169.58.32.179.nip.io`, and `https://*.169.58.32.179.nip.io`.
  - `CORS_ALLOWED_ORIGINS` updated with nip.io domains.
  - `MINIO_PUBLIC_ENDPOINT` set to `https://hexmedia-assets.169.58.32.179.nip.io`.
- **Verification**:
  - Traefik dynamically acquired Let's Encrypt certificate for both domains.
  - HTTP `http://hexmedia.169.58.32.179.nip.io` -> 308 redirect to HTTPS.
  - HTTPS `https://hexmedia.169.58.32.179.nip.io` -> HTTP/2 200 with valid TLS.
  - HTTPS `https://hexmedia-assets.169.58.32.179.nip.io/minio/health/live` -> HTTP/2 200 with valid TLS.
  - Unbroken continuity on `uggu.space` and `app.169.58.32.179.nip.io`.
