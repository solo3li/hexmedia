# TEST_READY: HexMedia Studio Comprehensive E2E Test Suite

## Test Suite Status: READY & VERIFIED

The opaque-box End-to-End (E2E) Test Suite for HexMedia Studio is implemented and verified against PostgreSQL 16 on port 5439 (`test_hexmedia` database).

- **Test Suite Location**: `/root/hexmedia/backend/ai_studio/tests_e2e.py`
- **Pytest Configuration**: `/root/hexmedia/pytest.ini` (`pythonpath = backend`, `DJANGO_SETTINGS_MODULE = hexmedia_core.settings`, `addopts = --reuse-db`)
- **Test Methodology & Architecture**: `/root/hexmedia/TEST_INFRA.md`
- **Execution Result**: 18 passed, 15 skipped (pending Milestones M2/M3), 0 failed in 27.24s (`exit code 0`).

---

## Runner Commands

### 1. Run Complete E2E Suite
```bash
./venv/bin/pytest backend/ai_studio/tests_e2e.py -v
```

### 2. Run by Tier
```bash
# Tier 1: Feature Coverage (happy paths for auth, chat, threads, titling, soft delete, memory, media library)
./venv/bin/pytest backend/ai_studio/tests_e2e.py -k "TestTier1FeatureCoverage" -v

# Tier 2: Boundary & Corner Cases (unauthenticated 401s, bad passwords, invalid tokens, cross-tenant isolation)
./venv/bin/pytest backend/ai_studio/tests_e2e.py -k "TestTier2BoundaryAndSecurity" -v

# Tier 3: Cross-Feature Interactions (auth + chat, thread titling + persistence, soft delete + media retention)
./venv/bin/pytest backend/ai_studio/tests_e2e.py -k "TestTier3CrossFeatureInteractions" -v

# Tier 4: Real-World Scenarios (visitor onboarding buffer flow, novel drama session lifecycle)
./venv/bin/pytest backend/ai_studio/tests_e2e.py -k "TestTier4RealWorldScenarios" -v
```

### 3. Rebuild Test Database from Scratch
```bash
./venv/bin/pytest backend/ai_studio/tests_e2e.py --create-db -v
```

### 4. Continuous Integration & Harness Gate
```bash
./init.sh
```

---

## 19-Feature Coverage Summary Table

| # | Feature Name | Milestone | Tier | Test Method in `tests_e2e.py` | Status |
|---|--------------|-----------|------|--------------------------------|--------|
| 1 | Hybrid Auth (Session + JWT) | M1 | Tier 1, 2 | `test_user_registration_returns_jwt_and_session`, `test_jwt_bearer_authentication_on_api` | PASSED |
| 2 | Auth Endpoints | M1 | Tier 1, 2 | `test_user_login_success`, `test_auth_logout`, `test_login_invalid_password_returns_401`, `test_login_nonexistent_user_returns_401` | PASSED |
| 3 | Model Ownership & Multi-Tenancy | M1 | Tier 1, 2 | `test_project_model_has_user_ownership`, `test_cross_tenant_project_isolation` | PASSED |
| 4 | API Endpoint Authorization Gates | M1 | Tier 2 | `test_anonymous_access_to_endpoints_returns_401`, `test_malformed_jwt_returns_401`, `test_expired_jwt_returns_401` | PASSED |
| 5 | Strict Cross-Tenant Access Gates | M1 | Tier 2 | `test_cross_tenant_project_isolation`, `test_cross_tenant_scene_mutation_blocked` | PASSED |
| 6 | ChatThread Master Container Model | M2 | Tier 1, 3 | `test_chat_thread_creation_and_attributes`, `test_auth_and_chat_thread_creation` | READY (Pending M2) |
| 7 | Thread CRUD Endpoints | M2 | Tier 1 | `test_thread_list_and_detail_crud`, `test_thread_rename` | READY (Pending M2) |
| 8 | AI Thread Titling | M2 | Tier 1, 3 | `test_thread_auto_titling_on_first_turn`, `test_thread_titling_and_message_persistence` | READY (Pending M2) |
| 9 | Soft Delete & Archival | M2 | Tier 1, 3 | `test_thread_soft_delete_preserves_records`, `test_soft_delete_preserves_project_media` | READY (Pending M2) |
| 10 | Bounded Sliding Window + Rolling Summary | M2 | Tier 1, 4 | `test_sliding_window_memory_bounded_turns`, `test_rolling_smart_summary` | READY (Pending M2) |
| 11 | LangGraph Postgres Checkpointing | M2 | Tier 1, 4 | `test_langgraph_checkpointer_persistence` | READY (Pending M2) |
| 12 | Studio Sidebar with Recency Groups | M3 | Tier 1, 3 | `test_sidebar_recency_grouping_logic` | READY (Pending M3) |
| 13 | Sidebar Search & Inline Actions | M3 | Tier 1 | `test_sidebar_search_filter_logic` | READY (Pending M3) |
| 14 | Auth Modals & Visitor Onboarding | M3 | Tier 4 | `test_visitor_onboarding_prompt_buffer_and_auth` | PASSED |
| 15 | Header Profile Menu & Logout | M3 | Tier 1 | `test_header_profile_data_contract` | PASSED |
| 16 | User Profile Media Management UI | M3 | Tier 1, 3 | `test_profile_media_endpoint_structure`, `test_soft_delete_preserves_project_media` | READY (Pending M3) |
| 17 | Profile Media API | M3 | Tier 1, 2 | `test_profile_media_endpoint_structure` | READY (Pending M3) |
| 18 | E2E Opaque-Box Test Suite | M4 | All | Full 4-Tier test execution in `backend/ai_studio/tests_e2e.py` | PASSED (0 failures) |
| 19 | Passing Verification Gates | M4 | All | Pytest passes with exit code 0; compileall passes | PASSED |

---

## Discovered Implementation Defect for Escalation
- **Location**: `backend/ai_studio/api.py:679` (`regenerate_scene_endpoint`) & `backend/ai_studio/tests.py:465` (`test_user_b_cannot_regenerate_user_a_scene`)
- **Observation**: Calling `POST /api/scenes/{scene_id}/regenerate` without an explicit JSON body causes Django Ninja's schema validator to reject the request with `HTTP 400 Bad Request` prior to reaching the tenant isolation check `get_object_or_404(Scene, id=scene_id, project__user=user)`.
- **Recommendation**: To ensure tenant isolation returns HTTP 404/403 even on empty bodies, check `get_object_or_404` before schema binding, or provide a default empty schema `data: RegenerateSceneRequest = RegenerateSceneRequest()`.
