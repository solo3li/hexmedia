# Dispatch: Test Writer (E2E Testing Track)

## Identity & Workspace
- Role: E2E Test Suite Designer & Implementer
- Working directory: /root/hexmedia/.agents/teamwork/teamwork_preview_test_writer_1
- Parent: f6e60383-d401-479c-9123-ee0a9cb852cc (teamwork_preview_orchestrator_1)

## Authoritative Inputs
- Read `/root/hexmedia/.agents/teamwork/ORIGINAL_REQUEST.md` completely.
- Read `/root/hexmedia/AGENTS.md` completely.
- Read `/root/hexmedia/PROJECT.md` completely.

## Objective
Design and implement the complete E2E Opaque-Box Test Suite for HexMedia Studio according to the 4-tier methodology:
1. Test Infra:
   - Configure `/root/hexmedia/pytest.ini` with `pythonpath = backend` and `DJANGO_SETTINGS_MODULE = hexmedia_core.settings`. Ensure `pytest-django` is installed in `./venv` if needed.
   - Author `/root/hexmedia/TEST_INFRA.md` following the template in `PROJECT.md`.
2. Test Suite Implementation:
   - Create comprehensive tests in `/root/hexmedia/backend/ai_studio/tests_e2e.py` (or modular test files):
     - **Tier 1 (Feature Coverage)**: Happy-path isolated tests for registration, login, JWT authentication, user profile, thread creation, titling, soft deletion, sliding window memory, LangGraph checkpointing, and media library API.
     - **Tier 2 (Boundary & Corner Cases)**: 401 for anonymous access to generation/mutation endpoints, invalid passwords, malformed JWTs, expired tokens, cross-tenant 403/404 isolation (User A cannot read/update/delete User B's projects or threads).
     - **Tier 3 (Cross-Feature Combinations)**: Auth + Chat session creation, Thread titling + rolling summary, Thread soft-delete retaining BookProject media.
     - **Tier 4 (Real-World Application Scenarios)**: Visitor onboarding workflow (prompt -> auth -> thread creation -> chat history reload), full audio drama generation lifecycle persistence.
3. Publish `/root/hexmedia/TEST_READY.md` containing runner command and coverage summary checklist.
4. Report back when ready.

## 2026-10-24T03:37:18Z
You are the E2E Test Suite Writer. Your working directory is /root/hexmedia/.agents/teamwork/teamwork_preview_test_writer_1.
Read /root/hexmedia/.agents/teamwork/ORIGINAL_REQUEST.md, /root/hexmedia/AGENTS.md, /root/hexmedia/PROJECT.md, and /root/hexmedia/.agents/teamwork/teamwork_preview_test_writer_1/DISPATCH.md.

Your objective is to build the comprehensive opaque-box E2E test suite:
1. Set up test infra: configure /root/hexmedia/pytest.ini (pythonpath = backend, DJANGO_SETTINGS_MODULE = hexmedia_core.settings) and ensure pytest can run tests cleanly against the PostgreSQL test database (port 5439, hexmedia_user has superuser/createdb).
2. Author /root/hexmedia/TEST_INFRA.md documenting the test methodology and feature mapping across all 19 features in PROJECT.md.
3. Implement test cases in /root/hexmedia/backend/ai_studio/tests_e2e.py across Tiers 1-4:
   - Tier 1: Feature Coverage (happy paths for auth, chat, threads, titling, soft delete, memory, media library)
   - Tier 2: Boundary & Corner Cases (unauthenticated 401s, bad passwords, invalid tokens, cross-tenant 403/404 isolation)
   - Tier 3: Cross-Feature Interactions (auth + chat threads, thread titling + message persistence, soft-delete + media preservation)
   - Tier 4: Real-World Application Scenarios (visitor onboarding buffer flow, full novel drama session lifecycle)
4. Publish /root/hexmedia/TEST_READY.md with runner commands and coverage summary table.
5. Send a message to parent (f6e60383-d401-479c-9123-ee0a9cb852cc) when TEST_READY.md is published.
Do NOT modify production backend/frontend implementation code outside of pytest.ini and test files.
