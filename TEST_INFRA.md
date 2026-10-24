# Test Infrastructure & Methodology: HexMedia Studio E2E Test Suite

## 1. Overview & Testing Philosophy

The HexMedia Studio End-to-End (E2E) Test Suite implements an **opaque-box testing methodology** designed to validate the system through its observable boundaries (HTTP REST APIs, session cookies, JWT bearer tokens, and persisted database states) without coupling to internal private methods.

### Core Testing Pillars
1. **Opaque-Box Verification**: Exercise public Django Ninja API endpoints (`/api/*`) and Django view routes using standard HTTP request/response semantics (`django.test.Client`).
2. **Real PostgreSQL Integration**: Execute all tests against the real PostgreSQL 16 database running on port 5439 (`test_hexmedia` database created dynamically with `hexmedia_user` superuser credentials). No in-memory SQLite approximations that mask Postgres-specific JSONField or concurrency nuances.
3. **Multi-Tenancy & Security Isolation**: Explicitly verify tenant boundary enforcement (User A vs. User B isolation, anonymous rejection with HTTP 401, cross-tenant rejection with HTTP 403/404).
4. **Deterministic & Isolated Tests**: Each test is self-contained, sets up its own user accounts and test data, cleans up after itself, and does not depend on execution order.

---

## 2. Test Environment Architecture

- **Runtime**: Python 3.12.3 in virtual environment (`./venv`)
- **Web Framework**: Django 6.1.2 + Django Ninja 1.7.1
- **Database Engine**: PostgreSQL 16 on `127.0.0.1:5439`, database `hexmedia` (test runner creates `test_hexmedia`)
- **Database Driver**: `psycopg` (psycopg 3.3.6)
- **Test Framework**: `pytest` 9.1.1 with `pytest-django` 4.14.0
- **Configuration**: `/root/hexmedia/pytest.ini`
  ```ini
  [pytest]
  DJANGO_SETTINGS_MODULE = hexmedia_core.settings
  pythonpath = backend
  python_files = tests.py test_*.py *_tests.py tests_*.py
  addopts = --reuse-db
  filterwarnings =
      ignore::DeprecationWarning
      ignore::UserWarning
  ```

---

## 3. 4-Tier Test Methodology

The test suite is structured across 4 hierarchical tiers to provide layered assurance:

### Tier 1: Feature Coverage (Unit & Happy Path Isolation)
Validates that each feature works according to specification under nominal conditions:
- **Auth**: User registration, login with credentials, JWT token generation, session cookie establishment, profile retrieval (`/api/auth/me`).
- **Threads**: Thread creation (`POST /api/threads`), listing (`GET /api/threads`), detail retrieval (`GET /api/threads/{id}`), manual update (`PATCH /api/threads/{id}`).
- **Memory & Titling**: Thread titling on first prompt, sliding window context calculation, rolling summary persistence.
- **Media & Soft Delete**: Soft deletion marking (`DELETE /api/threads/{id}` setting `is_deleted=True`), media library listing (`GET /api/profile/media`).

### Tier 2: Boundary & Corner Cases (Negative, Security & Fault Tolerance)
Tests system resiliency against invalid inputs, adversarial payloads, and unauthorized access:
- **Authentication Failures**: Anonymous requests to protected generation and mutation endpoints returning HTTP 401 Unauthorized.
- **Credential Validation**: Login attempts with non-existent email or wrong password returning HTTP 401.
- **JWT Malformation**: Requests with garbage tokens, expired tokens, or forged signatures rejected with HTTP 401.
- **Strict Cross-Tenant Isolation**: User A attempting to read, update, or delete User B's `BookProject`, `ChatThread`, or scenes returning HTTP 403 Forbidden or HTTP 404 Not Found.
- **Data Boundaries**: Empty prompts, oversized inputs, and non-existent IDs.

### Tier 3: Cross-Feature Interactions
Validates composite workflows that bridge multiple subsystems:
- **Auth + Chat Threads**: Authenticating via JWT and immediately creating a thread bound to that authenticated user.
- **Thread Titling + Message Persistence**: Sending the initial chat prompt, validating auto-titling occurs, and verifying message is persisted in database and reloaded.
- **Soft-Delete + Media Preservation**: Creating a project with scenes/audio tracks, soft-deleting the chat thread, and verifying the underlying `BookProject` media remains accessible via `/api/profile/media`.

### Tier 4: Real-World Application Scenarios
Simulates complete end-to-end user journeys:
- **Visitor Onboarding Buffer Flow**: Anonymous visitor inputs a prompt, UI/backend buffers prompt text, presents registration/login, user completes auth, and system automatically initializes the thread with the buffered prompt.
- **Novel Drama Lifecycle**: Full session flow from registration -> project creation -> character casting -> script/scenes -> thread reload across simulated session restarts.

---

## 4. Feature Mapping Matrix (19 Features from PROJECT.md)

| # | Feature Name | Milestone | Tier | Test Classes & Methods (`tests_e2e.py`) |
|---|--------------|-----------|------|-----------------------------------------|
| 1 | Hybrid Auth (Session + JWT) | M1 | Tier 1, 2 | `TestTier1FeatureCoverage::test_user_registration_returns_jwt_and_session`, `TestTier1FeatureCoverage::test_jwt_bearer_authentication_on_api` |
| 2 | Auth Endpoints | M1 | Tier 1, 2 | `TestTier1FeatureCoverage::test_auth_login_success`, `TestTier1FeatureCoverage::test_auth_logout`, `TestTier1FeatureCoverage::test_auth_me_endpoint`, `TestTier2BoundaryAndSecurity::test_login_invalid_password_returns_401` |
| 3 | Model Ownership & Multi-Tenancy | M1 | Tier 1, 2 | `TestTier1FeatureCoverage::test_project_model_has_user_ownership`, `TestTier2BoundaryAndSecurity::test_cross_tenant_project_isolation` |
| 4 | API Endpoint Authorization Gates | M1 | Tier 2 | `TestTier2BoundaryAndSecurity::test_anonymous_access_to_endpoints_returns_401`, `TestTier2BoundaryAndSecurity::test_malformed_jwt_returns_401` |
| 5 | Strict Cross-Tenant Access Gates | M1 | Tier 2 | `TestTier2BoundaryAndSecurity::test_cross_tenant_thread_isolation`, `TestTier2BoundaryAndSecurity::test_cross_tenant_scene_mutation_blocked` |
| 6 | ChatThread Master Container Model | M2 | Tier 1, 3 | `TestTier1FeatureCoverage::test_chat_thread_creation_and_attributes`, `TestTier3CrossFeatureInteractions::test_auth_and_chat_thread_creation` |
| 7 | Thread CRUD Endpoints | M2 | Tier 1 | `TestTier1FeatureCoverage::test_thread_list_and_detail_crud`, `TestTier1FeatureCoverage::test_thread_rename` |
| 8 | AI Thread Titling | M2 | Tier 1, 3 | `TestTier1FeatureCoverage::test_thread_auto_titling_on_first_turn`, `TestTier3CrossFeatureInteractions::test_thread_titling_and_message_persistence` |
| 9 | Soft Delete & Archival | M2 | Tier 1, 3 | `TestTier1FeatureCoverage::test_thread_soft_delete_preserves_records`, `TestTier3CrossFeatureInteractions::test_soft_delete_preserves_project_media` |
| 10 | Bounded Sliding Window + Rolling Summary | M2 | Tier 1, 4 | `TestTier1FeatureCoverage::test_sliding_window_memory_bounded_turns`, `TestTier1FeatureCoverage::test_rolling_smart_summary` |
| 11 | LangGraph Postgres Checkpointing | M2 | Tier 1, 4 | `TestTier1FeatureCoverage::test_langgraph_checkpointer_persistence` |
| 12 | Studio Sidebar with Recency Groups | M3 | Tier 1, 3 | `TestTier1FeatureCoverage::test_sidebar_recency_grouping_logic` |
| 13 | Sidebar Search & Inline Actions | M3 | Tier 1 | `TestTier1FeatureCoverage::test_sidebar_search_filter_logic` |
| 14 | Auth Modals & Visitor Onboarding | M3 | Tier 4 | `TestTier4RealWorldScenarios::test_visitor_onboarding_prompt_buffer_and_auth` |
| 15 | Header Profile Menu & Logout | M3 | Tier 1 | `TestTier1FeatureCoverage::test_header_profile_data_contract` |
| 16 | User Profile Media Management UI | M3 | Tier 1, 3 | `TestTier1FeatureCoverage::test_profile_media_library_contract`, `TestTier3CrossFeatureInteractions::test_soft_delete_preserves_project_media` |
| 17 | Profile Media API | M3 | Tier 1, 2 | `TestTier1FeatureCoverage::test_profile_media_endpoint_structure`, `TestTier2BoundaryAndSecurity::test_profile_media_unauthorized_returns_401` |
| 18 | E2E Opaque-Box Test Suite | M4 | All | Complete 4-Tier test suite execution in `backend/ai_studio/tests_e2e.py` |
| 19 | Passing Verification Gates | M4 | All | `./init.sh` runs cleanly, pytest exit code 0, compileall passes |

---

## 5. Execution Guide

### Full Suite Run
```bash
./venv/bin/pytest backend/ai_studio/tests_e2e.py -v
```

### Specific Tier Runs
```bash
# Tier 1: Feature Coverage
./venv/bin/pytest backend/ai_studio/tests_e2e.py -k "TestTier1" -v

# Tier 2: Boundary & Security
./venv/bin/pytest backend/ai_studio/tests_e2e.py -k "TestTier2" -v

# Tier 3: Cross-Feature Interactions
./venv/bin/pytest backend/ai_studio/tests_e2e.py -k "TestTier3" -v

# Tier 4: Real-World Scenarios
./venv/bin/pytest backend/ai_studio/tests_e2e.py -k "TestTier4" -v
```

### Clean Database Rebuild (if schema changed)
```bash
./venv/bin/pytest backend/ai_studio/tests_e2e.py --create-db -v
```

### Standard CI/Harness Verification
```bash
./init.sh
```
