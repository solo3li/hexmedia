# E2E Testing Orchestrator Dispatch

## Identity & Workspace
- Role: E2E Testing Orchestrator (Dual Track: Opaque-box Test Suite)
- Working directory: /root/hexmedia/.agents/teamwork/e2e_testing_orchestrator_1
- Parent: f6e60383-d401-479c-9123-ee0a9cb852cc (teamwork_preview_orchestrator_1)

## Authoritative Inputs
- Read `/root/hexmedia/.agents/teamwork/ORIGINAL_REQUEST.md` completely.
- Read `/root/hexmedia/AGENTS.md` completely.
- Read `/root/hexmedia/PROJECT.md` completely.

## Objective
Design and implement a comprehensive opaque-box automated test suite derived from user requirements and the Feature Inventory in `PROJECT.md`.
1. Set up test infrastructure (`pytest.ini` with `DJANGO_SETTINGS_MODULE = hexmedia_core.settings`, `pytest-django`, test database runner).
2. Author `TEST_INFRA.md` at project root documenting test architecture, methodology, and feature mapping.
3. Implement test cases using the 4-tier methodology:
   - Tier 1: Feature Coverage (happy path, isolation)
   - Tier 2: Boundary & Corner Cases (unauthenticated 401s, invalid payloads, missing headers, cross-tenant 403/404s)
   - Tier 3: Cross-Feature Combinations (auth + chat, thread creation + titling, soft delete + media retention)
   - Tier 4: Real-World Scenarios (visitor typing prompt -> auth -> auto session creation -> message history reload)
4. Publish `/root/hexmedia/TEST_READY.md` when the test suite is ready, containing runner instructions and coverage checklist.

Run the sub-orchestrator procedure (Assess -> Iterate with Worker/Reviewer/Challenger/Auditor) to build and verify tests.
Send a message back to parent when `TEST_READY.md` is published.
