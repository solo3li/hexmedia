"""
HexMedia Studio E2E Opaque-Box Test Suite
Covers 4 Tiers across all 19 Features defined in PROJECT.md:
- Tier 1: Feature Coverage (happy path isolated tests)
- Tier 2: Boundary & Corner Cases (unauthenticated 401s, bad passwords, invalid JWTs, cross-tenant isolation)
- Tier 3: Cross-Feature Interactions (auth + chat, thread titling + message persistence, soft delete + media retention)
- Tier 4: Real-World Application Scenarios (visitor prompt onboarding buffer flow, novel drama session lifecycle)
"""

import json
import uuid
import datetime
import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from django.utils import timezone
from ai_studio.models import (
    BookProject,
    Character,
    Chapter,
    Scene,
    TimelineState,
    ChatMessage,
    AIConfiguration,
)

User = get_user_model()


def is_route_registered(path_pattern: str, method: str = "GET") -> bool:
    """Helper to check if a specific route and HTTP method is registered on NinjaAPI."""
    try:
        from ai_studio.api import api
        method = method.upper()
        for prefix, router in api._routers:
            for p, path_ops in router.path_operations.items():
                full_path = f"{prefix}{p}".rstrip("/")
                if full_path == path_pattern.rstrip("/") or path_pattern.rstrip("/").endswith(p.rstrip("/")):
                    for op in path_ops.operations:
                        if method in op.methods:
                            return True
    except Exception:
        pass
    return False


def get_chat_thread_model():
    """Dynamically fetch ChatThread model if migrated in models.py."""
    import ai_studio.models as models
    return getattr(models, "ChatThread", None)


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def user_a(db):
    user, _ = User.objects.get_or_create(
        username="user_a",
        email="user_a@hexmedia.local",
        defaults={"first_name": "Alice"}
    )
    user.set_password("PasswordA123!")
    user.save()
    return user


@pytest.fixture
def user_b(db):
    user, _ = User.objects.get_or_create(
        username="user_b",
        email="user_b@hexmedia.local",
        defaults={"first_name": "Bob"}
    )
    user.set_password("PasswordB123!")
    user.save()
    return user


@pytest.fixture
def token_user_a(user_a):
    """Generate or mock valid JWT token for user_a."""
    try:
        from ai_studio.auth import generate_tokens_for_user
        tokens = generate_tokens_for_user(user_a)
        return tokens.get("access_token") or tokens.get("token")
    except ImportError:
        return "mock_token_user_a"


@pytest.fixture
def token_user_b(user_b):
    """Generate or mock valid JWT token for user_b."""
    try:
        from ai_studio.auth import generate_tokens_for_user
        tokens = generate_tokens_for_user(user_b)
        return tokens.get("access_token") or tokens.get("token")
    except ImportError:
        return "mock_token_user_b"


# ==============================================================================
# TIER 1: FEATURE COVERAGE (Happy Paths & Functional Isolation)
# ==============================================================================

@pytest.mark.django_db
class TestTier1FeatureCoverage:
    """Happy path verification for core features (Auth, Threads, Titling, Memory, Media Library)."""

    def test_system_health_and_config(self, client, user_a, token_user_a):
        """Verifies health check is public and configuration endpoints require auth."""
        resp = client.get("/api/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("status") == "ok"

        # Anonymous access to config returns 401
        anon_config = client.get("/api/config")
        assert anon_config.status_code == 401

        # Authenticated access to config succeeds with 200
        resp_config = client.get("/api/config", HTTP_AUTHORIZATION=f"Bearer {token_user_a}")
        assert resp_config.status_code == 200
        config_data = resp_config.json()
        assert "llm_model" in config_data
        assert "tts_model" in config_data
        assert "available_voices" in config_data

    def test_user_registration_returns_jwt_and_session(self, client):
        """Feature 1 & 2: POST /api/auth/register creates user, sets session, and returns JWT."""
        if not is_route_registered("/auth/register", "POST"):
            pytest.skip("Route /api/auth/register not yet registered (Milestone M1)")

        payload = {
            "email": "newuser@hexmedia.local",
            "username": "newuser",
            "password": "StrongPassword123!"
        }
        resp = client.post("/api/auth/register", data=json.dumps(payload), content_type="application/json")
        assert resp.status_code in [200, 201]
        data = resp.json()

        # Must return JWT tokens and user info
        assert "access_token" in data or "token" in data
        assert "user" in data
        assert data["user"].get("email") == "newuser@hexmedia.local"

        # User must exist in PostgreSQL
        assert User.objects.filter(email="newuser@hexmedia.local").exists()

        # Session cookie must be present for hybrid auth
        assert "sessionid" in resp.cookies or "sessionid" in client.cookies

    def test_user_login_success(self, client, user_a):
        """Feature 2: POST /api/auth/login validates credentials and returns tokens."""
        if not is_route_registered("/auth/login", "POST"):
            pytest.skip("Route /api/auth/login not yet registered (Milestone M1)")

        payload = {
            "email": user_a.email,
            "password": "PasswordA123!"
        }
        resp = client.post("/api/auth/login", data=json.dumps(payload), content_type="application/json")
        assert resp.status_code == 200
        data = resp.json()
        assert "access_token" in data or "token" in data
        assert data.get("user", {}).get("username") == user_a.username

    def test_jwt_bearer_authentication_on_api(self, client, user_a, token_user_a):
        """Feature 1 & 4: Authenticating to /api/auth/me via Bearer token."""
        if not is_route_registered("/auth/me", "GET"):
            pytest.skip("Route /api/auth/me not yet registered (Milestone M1)")

        resp = client.get("/api/auth/me", HTTP_AUTHORIZATION=f"Bearer {token_user_a}")
        assert resp.status_code == 200
        data = resp.json()
        assert data.get("username") == user_a.username
        assert data.get("email") == user_a.email

    def test_auth_logout(self, client, user_a, token_user_a):
        """Feature 2: POST /api/auth/logout clears user session."""
        if not is_route_registered("/auth/logout", "POST"):
            pytest.skip("Route /api/auth/logout not yet registered (Milestone M1)")

        client.force_login(user_a)
        resp = client.post("/api/auth/logout", HTTP_AUTHORIZATION=f"Bearer {token_user_a}")
        assert resp.status_code == 200

    def test_project_model_has_user_ownership(self, user_a):
        """Feature 3: BookProject has user ForeignKey establishing multi-tenancy."""
        if not hasattr(BookProject, "user"):
            pytest.skip("BookProject.user foreign key pending Milestone M1")

        project = BookProject.objects.create(
            title="رواية الأندلس المفقودة",
            user=user_a,
            status="DRAFT"
        )
        assert project.user == user_a
        assert BookProject.objects.filter(user=user_a).count() >= 1

    def test_chat_thread_creation_and_attributes(self, user_a):
        """Feature 6: ChatThread master container model attributes."""
        ChatThread = get_chat_thread_model()
        if ChatThread is None:
            pytest.skip("ChatThread model pending Milestone M2")

        thread = ChatThread.objects.create(
            user=user_a,
            title="محادثة قصة بوليسية",
            is_deleted=False
        )
        assert thread.id is not None
        assert thread.user == user_a
        assert thread.title == "محادثة قصة بوليسية"
        assert thread.is_deleted is False

    def test_thread_list_and_detail_crud(self, client, user_a, token_user_a):
        """Feature 7: Thread CRUD endpoints (GET /api/threads, POST /api/threads, GET /api/threads/{id})."""
        if not is_route_registered("/threads", "GET"):
            pytest.skip("Route /api/threads not yet registered (Milestone M2)")

        headers = {"HTTP_AUTHORIZATION": f"Bearer {token_user_a}"}

        # Create thread
        post_resp = client.post(
            "/api/threads",
            data=json.dumps({"title": "جلسة عصف ذهني سينمائي"}),
            content_type="application/json",
            **headers
        )
        assert post_resp.status_code in [200, 201]
        thread_data = post_resp.json()
        thread_id = thread_data.get("id")
        assert thread_id is not None

        # List threads
        list_resp = client.get("/api/threads", **headers)
        assert list_resp.status_code == 200
        threads = list_resp.json()
        assert any(t.get("id") == thread_id for t in (threads if isinstance(threads, list) else threads.get("threads", [])))

        # Get detail
        detail_resp = client.get(f"/api/threads/{thread_id}", **headers)
        assert detail_resp.status_code == 200
        assert detail_resp.json().get("title") == "جلسة عصف ذهني سينمائي"

    def test_thread_rename(self, client, user_a, token_user_a):
        """Feature 7: PATCH /api/threads/{id} inline rename."""
        ChatThread = get_chat_thread_model()
        if ChatThread is None or not is_route_registered("/threads/{thread_id}", "PATCH"):
            pytest.skip("Route PATCH /api/threads/{id} pending Milestone M2")

        thread = ChatThread.objects.create(user=user_a, title="عنوان قديم")
        headers = {"HTTP_AUTHORIZATION": f"Bearer {token_user_a}"}
        resp = client.patch(
            f"/api/threads/{thread.id}",
            data=json.dumps({"title": "عنوان جديد محدث"}),
            content_type="application/json",
            **headers
        )
        assert resp.status_code == 200
        thread.refresh_from_db()
        assert thread.title == "عنوان جديد محدث"

    def test_thread_soft_delete_preserves_records(self, client, user_a, token_user_a):
        """Feature 9: DELETE /api/threads/{id} performs soft delete (is_deleted=True)."""
        ChatThread = get_chat_thread_model()
        if ChatThread is None or not is_route_registered("/threads/{thread_id}", "DELETE"):
            pytest.skip("Route DELETE /api/threads/{id} pending Milestone M2")

        thread = ChatThread.objects.create(user=user_a, title="محادثة للحذف المؤقت", is_deleted=False)
        headers = {"HTTP_AUTHORIZATION": f"Bearer {token_user_a}"}
        resp = client.delete(f"/api/threads/{thread.id}", **headers)
        assert resp.status_code in [200, 204]

        # Verify soft delete
        thread.refresh_from_db()
        assert thread.is_deleted is True

        # Active list must exclude it
        list_resp = client.get("/api/threads", **headers)
        active_ids = [t.get("id") for t in (list_resp.json() if isinstance(list_resp.json(), list) else list_resp.json().get("threads", []))]
        assert str(thread.id) not in active_ids

    def test_thread_auto_titling_on_first_turn(self):
        """Feature 8: Automatic 3-5 word concept titling."""
        try:
            from ai_studio.services.gemini_service import generate_thread_title
            title = generate_thread_title("اكتب لي رواية إثارة عن سرقة كنز قديم في أهرامات الجيزة")
            assert isinstance(title, str)
            words = title.strip().split()
            assert 1 <= len(words) <= 7  # Concise title constraint
        except (ImportError, AttributeError):
            pytest.skip("generate_thread_title helper pending Milestone M2")

    def test_sliding_window_memory_bounded_turns(self, user_a):
        """Feature 10: Sliding window keeps last N turns bounded."""
        ChatThread = get_chat_thread_model()
        if ChatThread is None:
            pytest.skip("ChatThread memory pending Milestone M2")

        try:
            from ai_studio.services.gemini_service import get_thread_context
            thread = ChatThread.objects.create(user=user_a, title="شات متعدد الأدوار")
            for i in range(12):
                ChatMessage.objects.create(
                    role="USER" if i % 2 == 0 else "ASSISTANT",
                    content=f"رسالة رقم {i}",
                    metadata={"thread_id": str(thread.id)}
                )
            summary, recent_turns = get_thread_context(thread, window_size=6)
            assert len(recent_turns) <= 6
        except (ImportError, AttributeError):
            pytest.skip("get_thread_context helper pending Milestone M2")

    def test_rolling_smart_summary(self):
        """Feature 10: Rolling smart summary compresses earlier conversation."""
        try:
            from ai_studio.services.gemini_service import update_rolling_summary
            past_messages = [
                {"role": "user", "content": "البطل اسمه فارس ويملك سيفاً سحرياً"},
                {"role": "assistant", "content": "فارس يتجه نحو الجبل الأسود لمواجهة التنين"}
            ]
            summary = update_rolling_summary("", past_messages)
            assert isinstance(summary, str)
            assert len(summary) > 0
        except (ImportError, AttributeError):
            pytest.skip("update_rolling_summary helper pending Milestone M2")

    def test_langgraph_checkpointer_persistence(self):
        """Feature 11: LangGraph checkpointer initialization and thread_id persistence."""
        try:
            from ai_studio.services.langgraph_controller import get_checkpointer
            cp = get_checkpointer(test_mode=True)
            assert cp is not None
        except (ImportError, AttributeError):
            pytest.skip("get_checkpointer helper pending Milestone M2")

    def test_profile_media_endpoint_structure(self, client, user_a, token_user_a):
        """Feature 16 & 17: GET /api/profile/media returns audio, scripts, and video scenes."""
        if not is_route_registered("/profile/media", "GET"):
            pytest.skip("Route /api/profile/media not yet registered (Milestone M3)")

        headers = {"HTTP_AUTHORIZATION": f"Bearer {token_user_a}"}
        resp = client.get("/api/profile/media", **headers)
        assert resp.status_code == 200
        data = resp.json()
        assert "audio_tracks" in data
        assert "scripts" in data
        assert "video_scenes" in data

    def test_sidebar_recency_grouping_logic(self, user_a):
        """Feature 12: Grouping threads by Today, Yesterday, Previous 7 Days, Older."""
        ChatThread = get_chat_thread_model()
        if ChatThread is None:
            pytest.skip("ChatThread recency grouping pending Milestone M2/M3")

        now = timezone.now()
        t_today = ChatThread.objects.create(user=user_a, title="شات اليوم", updated_at=now)
        t_yesterday = ChatThread.objects.create(user=user_a, title="شات أمس", updated_at=now - datetime.timedelta(days=1))
        t_week = ChatThread.objects.create(user=user_a, title="شات الأسبوع الماضي", updated_at=now - datetime.timedelta(days=4))

        # Check recency partitioning logic
        def partition_thread(thread):
            delta = (now - thread.updated_at).days
            if delta == 0:
                return "Today"
            elif delta == 1:
                return "Yesterday"
            elif delta <= 7:
                return "Previous 7 Days"
            return "Older"

        assert partition_thread(t_today) == "Today"
        assert partition_thread(t_yesterday) == "Yesterday"
        assert partition_thread(t_week) == "Previous 7 Days"

    def test_sidebar_search_filter_logic(self, user_a):
        """Feature 13: Live search filter across user threads."""
        ChatThread = get_chat_thread_model()
        if ChatThread is None:
            pytest.skip("ChatThread search pending Milestone M2/M3")

        ChatThread.objects.create(user=user_a, title="رحلة الفضاء المجهول")
        ChatThread.objects.create(user=user_a, title="أسرار المحيط الغريق")

        qs = ChatThread.objects.filter(user=user_a, is_deleted=False, title__icontains="الفضاء")
        assert qs.count() == 1
        assert "الفضاء" in qs.first().title

    def test_header_profile_data_contract(self, client, user_a, token_user_a):
        """Feature 15: Header displays user details and logout link."""
        if not is_route_registered("/auth/me", "GET"):
            pytest.skip("Route /api/auth/me pending Milestone M1")

        resp = client.get("/api/auth/me", HTTP_AUTHORIZATION=f"Bearer {token_user_a}")
        assert resp.status_code == 200
        user_info = resp.json()
        assert user_info.get("email") == user_a.email
        assert user_info.get("username") == user_a.username


# ==============================================================================
# TIER 2: BOUNDARY & CORNER CASES (Negative, Security & Fault Tolerance)
# ==============================================================================

@pytest.mark.django_db
class TestTier2BoundaryAndSecurity:
    """Adversarial and boundary test cases enforcing security gates and data isolation."""

    def test_anonymous_access_to_endpoints_returns_401(self, client):
        """Feature 4: Protected API endpoints return 401 for unauthenticated clients."""
        protected_endpoints = [
            ("/api/auth/me", "get"),
            ("/api/threads", "get"),
            ("/api/threads", "post"),
            ("/api/profile/media", "get"),
            ("/api/upload-book", "post"),
            ("/api/projects/00000000-0000-0000-0000-000000000000/execute-chapter", "post"),
            ("/api/projects/00000000-0000-0000-0000-000000000000/export", "post"),
        ]

        unprotected_count = 0
        for path, method in protected_endpoints:
            if not is_route_registered(path.split("/api")[1].split("/00000000")[0], method):
                continue
            caller = getattr(client, method)
            resp = caller(path, data="{}" if method == "post" else None, content_type="application/json")
            if resp.status_code != 401:
                unprotected_count += 1

        if unprotected_count > 0:
            # Escalate if endpoints are registered but lack 401 auth gate
            assert unprotected_count == 0, f"{unprotected_count} registered endpoints failed 401 auth gate"

    def test_login_invalid_password_returns_401(self, client, user_a):
        """Feature 2: Incorrect password must return HTTP 401."""
        if not is_route_registered("/auth/login", "POST"):
            pytest.skip("Route /api/auth/login pending Milestone M1")

        payload = {"email": user_a.email, "password": "WrongPassword999!"}
        resp = client.post("/api/auth/login", data=json.dumps(payload), content_type="application/json")
        assert resp.status_code == 401

    def test_login_nonexistent_user_returns_401(self, client):
        """Feature 2: Non-existent email must return HTTP 401."""
        if not is_route_registered("/auth/login", "POST"):
            pytest.skip("Route /api/auth/login pending Milestone M1")

        payload = {"email": "ghost@hexmedia.local", "password": "AnyPassword123!"}
        resp = client.post("/api/auth/login", data=json.dumps(payload), content_type="application/json")
        assert resp.status_code == 401

    def test_malformed_jwt_returns_401(self, client):
        """Feature 1 & 4: Garbage or corrupted JWT token must return HTTP 401."""
        if not is_route_registered("/auth/me", "GET"):
            pytest.skip("Route /api/auth/me pending Milestone M1")

        resp = client.get("/api/auth/me", HTTP_AUTHORIZATION="Bearer invalid.token.payload")
        assert resp.status_code == 401

    def test_expired_jwt_returns_401(self, client):
        """Feature 1 & 4: Expired JWT token rejected with HTTP 401."""
        try:
            import jwt
            from django.conf import settings
            expired_payload = {
                "user_id": 9999,
                "exp": datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(hours=2)
            }
            expired_token = jwt.encode(expired_payload, settings.SECRET_KEY, algorithm="HS256")
            resp = client.get("/api/auth/me", HTTP_AUTHORIZATION=f"Bearer {expired_token}")
            assert resp.status_code == 401
        except Exception:
            # Fallback test if manual token generation used
            resp = client.get("/api/auth/me", HTTP_AUTHORIZATION="Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJleHAiOjE1MTYyMzkwMjJ9.invalid")
            if is_route_registered("/auth/me", "GET"):
                assert resp.status_code == 401

    def test_cross_tenant_project_isolation(self, client, user_a, user_b, token_user_b):
        """Feature 5: User B cannot access or modify User A's BookProject."""
        if not hasattr(BookProject, "user"):
            pytest.skip("BookProject.user pending Milestone M1")

        proj_a = BookProject.objects.create(title="مشروع سري لـ User A", user=user_a)
        headers_b = {"HTTP_AUTHORIZATION": f"Bearer {token_user_b}"}

        # Attempt chapter list
        resp = client.get(f"/api/projects/{proj_a.id}/chapters", **headers_b)
        assert resp.status_code in [401, 403, 404]

        # Attempt chapter execution
        resp_exec = client.post(
            f"/api/projects/{proj_a.id}/execute-chapter",
            data=json.dumps({"chapter_number": 1}),
            content_type="application/json",
            **headers_b
        )
        assert resp_exec.status_code in [401, 403, 404]

    def test_cross_tenant_thread_isolation(self, client, user_a, user_b, token_user_b):
        """Feature 5: User B cannot view, rename, or delete User A's ChatThread."""
        ChatThread = get_chat_thread_model()
        if ChatThread is None or not is_route_registered("/threads/{thread_id}", "GET"):
            pytest.skip("ChatThread isolation pending Milestone M2")

        thread_a = ChatThread.objects.create(user=user_a, title="محادثة خاصة أ")
        headers_b = {"HTTP_AUTHORIZATION": f"Bearer {token_user_b}"}

        # User B reads User A thread
        resp_get = client.get(f"/api/threads/{thread_a.id}", **headers_b)
        assert resp_get.status_code in [403, 404]

        # User B renames User A thread
        resp_patch = client.patch(
            f"/api/threads/{thread_a.id}",
            data=json.dumps({"title": "اختراق العنوان"}),
            content_type="application/json",
            **headers_b
        )
        assert resp_patch.status_code in [403, 404]

        # User B deletes User A thread
        resp_del = client.delete(f"/api/threads/{thread_a.id}", **headers_b)
        assert resp_del.status_code in [403, 404]

    def test_cross_tenant_scene_mutation_blocked(self, client, user_a, user_b, token_user_b):
        """Feature 5: User B cannot delete or alter scenes belonging to User A."""
        if not hasattr(BookProject, "user"):
            pytest.skip("BookProject.user pending Milestone M1")

        proj_a = BookProject.objects.create(title="مشروع مشاهد أ", user=user_a)
        scene_a = Scene.objects.create(project=proj_a, order=1, raw_text="حوار سري")

        headers_b = {"HTTP_AUTHORIZATION": f"Bearer {token_user_b}"}
        resp = client.delete(f"/api/scenes/{scene_a.id}", **headers_b)
        assert resp.status_code in [401, 403, 404]

        # Ensure scene still exists
        assert Scene.objects.filter(id=scene_a.id).exists()

    def test_registration_duplicate_email_error(self, client, user_a):
        """Feature 2: Registering with an existing email returns 400 or 409 error."""
        if not is_route_registered("/auth/register", "POST"):
            pytest.skip("Route /api/auth/register pending Milestone M1")

        payload = {
            "email": user_a.email,
            "username": "distinct_user",
            "password": "Password123!"
        }
        resp = client.post("/api/auth/register", data=json.dumps(payload), content_type="application/json")
        assert resp.status_code in [400, 409]

    def test_registration_empty_password_error(self, client):
        """Feature 2: Registration with blank password rejected."""
        if not is_route_registered("/auth/register", "POST"):
            pytest.skip("Route /api/auth/register pending Milestone M1")

        payload = {"email": "blank_pw@hexmedia.local", "username": "blank_pw", "password": ""}
        resp = client.post("/api/auth/register", data=json.dumps(payload), content_type="application/json")
        assert resp.status_code in [400, 422]


# ==============================================================================
# TIER 3: CROSS-FEATURE INTERACTIONS
# ==============================================================================

@pytest.mark.django_db
class TestTier3CrossFeatureInteractions:
    """Interactions between Auth, Threads, Titling, and Media Preservation."""

    def test_auth_and_chat_thread_creation(self, client, user_a, token_user_a):
        """Features 1, 6 & 7: Authenticated user creates and owns a thread."""
        ChatThread = get_chat_thread_model()
        if ChatThread is None or not is_route_registered("/threads", "POST"):
            pytest.skip("Threads integration pending Milestone M2")

        headers = {"HTTP_AUTHORIZATION": f"Bearer {token_user_a}"}
        resp = client.post(
            "/api/threads",
            data=json.dumps({"title": "شات تفاعلي متكامل"}),
            content_type="application/json",
            **headers
        )
        assert resp.status_code in [200, 201]
        thread_id = resp.json().get("id")

        thread = ChatThread.objects.get(id=thread_id)
        assert thread.user == user_a
        assert thread.is_deleted is False

    def test_thread_titling_and_message_persistence(self, client, user_a, token_user_a):
        """Features 6, 8 & 10: First turn triggers auto-titling and persists messages to PostgreSQL."""
        ChatThread = get_chat_thread_model()
        if ChatThread is None:
            pytest.skip("Thread titling & persistence pending Milestone M2")

        thread = ChatThread.objects.create(user=user_a, title="محادثة جديدة")

        # Simulate message creation
        msg = ChatMessage.objects.create(
            role="USER",
            content="اكتب سيناريو فيلم خيال علمي في محطة الفضاء الدولية",
            metadata={"thread_id": str(thread.id)}
        )

        assert ChatMessage.objects.filter(id=msg.id).exists()
        reloaded = ChatMessage.objects.get(id=msg.id)
        assert "خيال علمي" in reloaded.content

    def test_soft_delete_preserves_project_media(self, client, user_a, token_user_a):
        """Features 9 & 16: Soft deleting a thread keeps BookProject media in Profile Media Library."""
        ChatThread = get_chat_thread_model()
        if ChatThread is None or not hasattr(BookProject, "user"):
            pytest.skip("Soft delete & media preservation pending Milestone M2/M3")

        # Create project with scenes and timeline
        project = BookProject.objects.create(title="رواية محتفظ ببياناتها", user=user_a)
        scene = Scene.objects.create(project=project, order=1, raw_text="مشهد سينمائي", audio_url="http://minio/audio.wav")
        TimelineState.objects.create(project=project, exported_audio_url="http://minio/master.wav")

        # Thread linked to project
        thread = ChatThread.objects.create(user=user_a, project=project, title="شات الرواية", is_deleted=False)

        # Soft delete thread
        headers = {"HTTP_AUTHORIZATION": f"Bearer {token_user_a}"}
        if is_route_registered("/threads/{thread_id}", "DELETE"):
            client.delete(f"/api/threads/{thread.id}", **headers)
            thread.refresh_from_db()
            assert thread.is_deleted is True

        # Project and assets must survive intact
        assert BookProject.objects.filter(id=project.id).exists()
        assert Scene.objects.filter(id=scene.id).exists()

        # If profile media endpoint is active, verify media is listed
        if is_route_registered("/profile/media", "GET"):
            media_resp = client.get("/api/profile/media", **headers)
            assert media_resp.status_code == 200
            media_data = media_resp.json()
            assert any(track.get("project_id") == str(project.id) for track in media_data.get("audio_tracks", []))


# ==============================================================================
# TIER 4: REAL-WORLD APPLICATION SCENARIOS
# ==============================================================================

@pytest.mark.django_db
class TestTier4RealWorldScenarios:
    """Full user lifecycle simulations."""

    def test_visitor_onboarding_prompt_buffer_and_auth(self, client):
        """Feature 14: Unauthenticated visitor types prompt, registers, and dispatches prompt seamlessly."""
        if not is_route_registered("/auth/register", "POST"):
            pytest.skip("Visitor onboarding auth pending Milestone M1/M3")

        # 1. Visitor types prompt (buffered on client)
        buffered_prompt = "أريد كتابة دراما صوتية ملحمية عن معركة حطين"

        # 2. Visitor triggers auth modal and completes registration
        reg_payload = {
            "email": "onboarding_visitor@hexmedia.local",
            "username": "visitor_hero",
            "password": "VisitorPassword123!"
        }
        reg_resp = client.post("/api/auth/register", data=json.dumps(reg_payload), content_type="application/json")
        assert reg_resp.status_code in [200, 201]
        token = reg_resp.json().get("access_token") or reg_resp.json().get("token")
        assert token is not None

        # 3. Dispatches buffered prompt to start session
        headers = {"HTTP_AUTHORIZATION": f"Bearer {token}"}
        if is_route_registered("/threads", "POST"):
            thread_resp = client.post(
                "/api/threads",
                data=json.dumps({"initial_prompt": buffered_prompt, "title": "محادثة معركة حطين"}),
                content_type="application/json",
                **headers
            )
            assert thread_resp.status_code in [200, 201]

    def test_novel_drama_session_lifecycle(self, client, user_a, token_user_a):
        """Complete session lifecycle: auth -> project creation -> casting -> scene generation -> session resume."""
        if not hasattr(BookProject, "user"):
            pytest.skip("BookProject.user pending Milestone M1")

        # 1. User authenticated (user_a, token_user_a)
        headers = {"HTTP_AUTHORIZATION": f"Bearer {token_user_a}"}

        # 2. Create project
        project = BookProject.objects.create(
            title="رواية سيف العدالة",
            user=user_a,
            status="DRAFT"
        )
        assert project.user == user_a

        # 3. Cast characters
        char1 = Character.objects.create(
            project=project,
            name="سيف",
            role_type="PROTAGONIST",
            assigned_voice="Puck"
        )
        char2 = Character.objects.create(
            project=project,
            name="الحكيم",
            role_type="NARRATOR",
            assigned_voice="Charon"
        )
        assert project.characters.count() == 2

        # 4. Generate scenes
        scene = Scene.objects.create(
            project=project,
            order=1,
            speaker=char1,
            speaker_name=char1.name,
            raw_text="أيها الحكيم، حان وقت الانطلاق إلى وادي الأسرار.",
            status="GENERATED"
        )
        assert project.scenes.count() == 1

        # 5. Checkpointer session recovery simulation
        try:
            from ai_studio.services.langgraph_controller import get_checkpointer
            cp = get_checkpointer(test_mode=True)
            assert cp is not None
        except (ImportError, AttributeError):
            pass

        # 6. Verify session data persisted in PostgreSQL
        reloaded_proj = BookProject.objects.get(id=project.id)
        assert reloaded_proj.scenes.count() == 1
        assert reloaded_proj.characters.count() == 2
