# Original User Request

## 2026-10-24T03:26:08Z

Implement a multi-user authentication system (hybrid Django Session + JWT) and a ChatGPT-style conversation memory architecture with LangGraph state persistence, collapsible session sidebar, AI thread titling, seamless visitor prompt onboarding, and user profile media manager in HexMedia Studio.

Working directory: /root/hexmedia
Integrity mode: development

## Requirements

### R1. Multi-User Authentication & Data Isolation
- Email and password registration, login, and logout with immediate automatic login upon registration.
- Hybrid authentication: standard Django session cookies for admin and template views, and JWT tokens (stored in localStorage and sent via Authorization headers) for Django Ninja API endpoints.
- Strict multi-tenancy data isolation: every BookProject, Scene, Character, ChatThread, and audio/video asset is strictly owned by the authenticated user; cross-user access is prohibited.
- Auth UI: sleek modal dialogs (Login & Register) integrated directly into the current studio interface, plus a user profile menu with logout in the top navigation.
- Seamless visitor onboarding: if an unauthenticated visitor types a prompt, preserve their text in the input buffer, present the auth modal, and automatically initialize the conversation session with that prompt immediately upon successful login/register.

### R2. ChatGPT-Style Conversation Thread Architecture & Memory
- Conversation session as master container: each thread owns its message history, novel/script generation, character voice casting, and timeline assets.
- Automatic AI thread titling: the first message in a thread triggers automatic generation of a 3-5 word concise title reflecting the story concept, with inline manual rename and deletion capabilities.
- Soft delete & archival: deleting a thread removes it from the active sidebar while retaining project data accessible in the user profile media library.
- Context window management: sliding window of the last N turns combined with rolling smart summaries of earlier conversation to keep prompts concise and token-efficient.

### R3. LangGraph State & Checkpoint Persistence
- Integrate LangGraph state checkpointing (PostgresSaver / database checkpointer) keyed by unique thread_id per conversation and user.
- Ensure graph state can be resumed across sessions without losing intermediate dramatization steps, character mappings, or rendering jobs.

### R4. Studio Sidebar & Profile Media Management UI
- Collapsible left sidebar in the chat studio displaying past conversation threads grouped by recency (Today, Yesterday, Previous 7 Days), with active indicator, search filter, and quick action icons (rename, delete).
- User Profile page or modal with a "My Projects & Media" section where users can browse, play, and download all generated audio drama master tracks, novel scripts, and video scenes.

## Acceptance Criteria

### Authentication & Isolation
- [ ] Anonymous users accessing generation endpoints receive HTTP 401 Unauthorized.
- [ ] Registration with valid email and password creates user and returns valid JWT token and session cookie.
- [ ] Login endpoint validates credentials, rejecting incorrect passwords with HTTP 401.
- [ ] User A cannot view, retrieve, edit, or delete any project, thread, or audio file belonging to User B (HTTP 403 or 404).

### Conversation & Memory Persistence
- [ ] Submitting the first message in a new session automatically generates and assigns a title to the thread.
- [ ] Messages submitted in a thread are persisted in PostgreSQL and reloaded accurately upon page refresh or thread switching.
- [ ] LangGraph engine recovers previous turn state and character assignments for subsequent messages within the same thread.
- [ ] Context size remains bounded: sliding window with summary compression ensures token usage does not exceed maximum limit.

### UI & Seamless Experience
- [ ] Studio interface features a collapsible sidebar listing all user threads with live search and rename/delete options.
- [ ] Unauthenticated prompt input preserves user text, presents the login/register modal, and dispatches the prompt immediately upon successful authentication.
- [ ] User profile interface provides a dedicated media library displaying all generated audio and project deliverables with direct playback and download links.

### Verification & Automated Testing
- [ ] Automated test suite verifies auth endpoints (register, login, token refresh, isolation gates).
- [ ] Automated test suite verifies conversation message persistence and thread switching.
- [ ] `./init.sh` runs cleanly and passes all verification gates.
