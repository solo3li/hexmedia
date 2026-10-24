import json
import uuid
import time
import threading
from concurrent.futures import ThreadPoolExecutor
from django.test import TestCase, Client, TransactionTestCase
from django.contrib.auth import get_user_model
from django.db import connection, IntegrityError
from ai_studio.models import (
    BookProject,
    Character,
    Chapter,
    Scene,
    TimelineState,
    ChatMessage,
)
from ai_studio.auth import (
    create_jwt_token,
    decode_jwt_payload,
    decode_jwt_token,
    generate_tokens_for_user,
    _b64url_encode,
)

User = get_user_model()


class DuplicateRegistrationStressTests(TestCase):
    """
    Stress tests for user registration: duplicate emails, usernames, casing,
    whitespace trimming, and concurrent registration attempts.
    """
    def setUp(self):
        self.client = Client()
        self.existing_user = User.objects.create_user(
            username="hero_user",
            email="hero@hexmedia.local",
            password="StrongPassword123"
        )

    def test_duplicate_exact_email_rejected_with_400(self):
        res = self.client.post(
            "/api/auth/register",
            data=json.dumps({
                "email": "hero@hexmedia.local",
                "password": "AnotherPassword456"
            }),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("مسجل بالفعل", res.json().get("detail", ""))

    def test_duplicate_email_case_insensitivity_and_whitespace(self):
        # Email with uppercase and leading/trailing whitespace
        res = self.client.post(
            "/api/auth/register",
            data=json.dumps({
                "email": "  HERO@HEXMEDIA.LOCAL  ",
                "password": "AnotherPassword456"
            }),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("مسجل بالفعل", res.json().get("detail", ""))

    def test_duplicate_username_automatically_generates_unique_suffix(self):
        # Register user with same username 'hero_user' but different email
        res = self.client.post(
            "/api/auth/register",
            data=json.dumps({
                "username": "hero_user",
                "email": "new_hero@hexmedia.local",
                "password": "Password789"
            }),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["user"]["username"], "hero_user_1")
        self.assertEqual(data["user"]["email"], "new_hero@hexmedia.local")

        # Third user with same username gets _2
        res2 = self.client.post(
            "/api/auth/register",
            data=json.dumps({
                "username": "hero_user",
                "email": "another_hero@hexmedia.local",
                "password": "Password789"
            }),
            content_type="application/json"
        )
        self.assertEqual(res2.status_code, 200)
        self.assertEqual(res2.json()["user"]["username"], "hero_user_2")

    def test_registration_with_empty_or_whitespace_fields(self):
        # Empty password
        res1 = self.client.post(
            "/api/auth/register",
            data=json.dumps({"email": "blank_pw@hexmedia.local", "password": ""}),
            content_type="application/json"
        )
        self.assertEqual(res1.status_code, 400)

        # Whitespace password
        res2 = self.client.post(
            "/api/auth/register",
            data=json.dumps({"email": "space_pw@hexmedia.local", "password": "   "}),
            content_type="application/json"
        )
        self.assertEqual(res2.status_code, 400)

        # Invalid emails
        for bad_email in ["notanemail", "@nodomain", "user@", ""]:
            res = self.client.post(
                "/api/auth/register",
                data=json.dumps({"email": bad_email, "password": "ValidPassword123"}),
                content_type="application/json"
            )
            self.assertEqual(res.status_code, 400)


class ConcurrentRegistrationStressTests(TransactionTestCase):
    """
    Empirical concurrency test for simultaneous registrations with identical credentials.
    """
    def test_concurrent_registrations_same_email(self):
        # Spawn multiple concurrent requests registering the exact same email
        email = f"concurrent_race_{uuid.uuid4().hex[:8]}@hexmedia.local"
        password = "RaceConditionPass123"
        results = []

        def register_worker():
            from django.db import connection
            c = Client()
            try:
                res = c.post(
                    "/api/auth/register",
                    data=json.dumps({"email": email, "password": password}),
                    content_type="application/json"
                )
                return res.status_code
            except Exception as e:
                return type(e).__name__
            finally:
                connection.close()

        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = [executor.submit(register_worker) for _ in range(5)]
            results = [f.result() for f in futures]

        # Exactly one should succeed (200), all others should be rejected (400)
        success_count = results.count(200)
        rejected_count = results.count(400)
        self.assertEqual(success_count, 1, f"Expected 1 success, got {success_count}. Results: {results}")
        self.assertEqual(rejected_count, 4, f"Expected 4 rejections, got {rejected_count}. Results: {results}")

        # In DB, exactly one user with this email should exist
        self.assertEqual(User.objects.filter(email__iexact=email).count(), 1)


class RefreshTokenSecurityAndMechanicsTests(TestCase):
    """
    Adversarial security tests for token refresh and misuse:
    - Refresh tokens used as Bearer access tokens
    - Access tokens used as refresh tokens
    - Expired, tampered, and 'alg: none' JWT attacks
    - Tokens for deactivated accounts
    """
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="security_target",
            email="security@hexmedia.local",
            password="SecurePass123!"
        )
        self.tokens = generate_tokens_for_user(self.user)
        self.access_token = self.tokens["access_token"]
        self.refresh_token = self.tokens["refresh_token"]

    def test_refresh_token_CANNOT_be_used_as_bearer_access_token_on_me(self):
        # Sending refresh token in Authorization: Bearer <refresh_token> must fail
        res = self.client.get(
            "/api/auth/me",
            HTTP_AUTHORIZATION=f"Bearer {self.refresh_token}"
        )
        self.assertEqual(res.status_code, 401)

    def test_refresh_token_CANNOT_be_used_as_bearer_on_projects(self):
        res = self.client.get(
            "/api/projects",
            HTTP_AUTHORIZATION=f"Bearer {self.refresh_token}"
        )
        self.assertEqual(res.status_code, 401)

    def test_refresh_token_CANNOT_be_used_as_bearer_on_chat(self):
        res = self.client.post(
            "/api/chat",
            data=json.dumps({"prompt": "Hello"}),
            content_type="application/json",
            HTTP_AUTHORIZATION=f"Bearer {self.refresh_token}"
        )
        self.assertEqual(res.status_code, 401)

    def test_access_token_CANNOT_be_used_at_refresh_endpoint(self):
        # Sending access_token to /api/auth/refresh must fail
        res = self.client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh_token": self.access_token}),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 401)
        self.assertIn("غير صالح", res.json().get("detail", ""))

    def test_expired_refresh_token_rejected_at_refresh_endpoint(self):
        # Craft an expired refresh token
        expired_refresh = create_jwt_token(
            {"user_id": self.user.id, "token_type": "refresh"},
            expires_in_seconds=-60
        )
        res = self.client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh_token": expired_refresh}),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 401)

    def test_tampered_refresh_token_rejected(self):
        parts = self.refresh_token.split('.')
        # Tamper payload
        tampered = f"{parts[0]}.eyAidXNlcl9pZCI6IDk5OSwgInRva2VuX3R5cGUiOiAicmVmcmVzaCIgfQ.{parts[2]}"
        res = self.client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh_token": tampered}),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 401)

    def test_jwt_alg_none_attack_rejected(self):
        # Craft header with alg: none
        hdr_b64 = _b64url_encode(b'{"alg":"none","typ":"JWT"}')
        payload_b64 = _b64url_encode(json.dumps({
            "user_id": self.user.id,
            "token_type": "access",
            "exp": int(time.time()) + 3600
        }).encode('utf-8'))
        none_token = f"{hdr_b64}.{payload_b64}."

        res = self.client.get(
            "/api/auth/me",
            HTTP_AUTHORIZATION=f"Bearer {none_token}"
        )
        self.assertEqual(res.status_code, 401)

    def test_deactivated_user_cannot_refresh_or_access_endpoints(self):
        # Deactivate user
        self.user.is_active = False
        self.user.save()

        # Access token must now fail
        res_me = self.client.get(
            "/api/auth/me",
            HTTP_AUTHORIZATION=f"Bearer {self.access_token}"
        )
        self.assertEqual(res_me.status_code, 401)

        # Refresh token must also fail
        res_ref = self.client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh_token": self.refresh_token}),
            content_type="application/json"
        )
        self.assertEqual(res_ref.status_code, 401)

    def test_malformed_authorization_headers(self):
        bad_headers = [
            "Bearer",
            "Bearer ",
            "Bearer not.enough.parts",
            "Bearer too.many.parts.in.this.token.here",
            "Basic YWRtaW46cGFzc3dvcmQ=",
            "Token something",
            "Bearer invalid_base64_???_characters",
        ]
        for bh in bad_headers:
            res = self.client.get("/api/auth/me", HTTP_AUTHORIZATION=bh)
            self.assertEqual(res.status_code, 401, f"Header '{bh}' did not return 401")


class HybridAuthCombinationsTests(TestCase):
    """
    Exhaustive empirical testing of hybrid authentication combinations:
    1. Neither session cookie nor Bearer token -> 401
    2. Session cookie only (no Bearer) -> 200 (authenticated as Session user)
    3. Bearer token only (no session cookie) -> 200 (authenticated as Bearer user)
    4. Both present and matching -> 200
    5. Both present and CONFLICTING:
       Session cookie is User A, Bearer token is User B.
       Verify precedence: Bearer token takes priority in NinjaAPI,
       request.auth is User B, and User B CANNOT see User A's data.
    6. Valid Session + Invalid Bearer token:
       Bearer fails verification, fall back to Session cookie? Or 401?
    """
    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(
            username="hybrid_user_a",
            email="hybrid_a@hexmedia.local",
            password="PasswordA123"
        )
        self.user_b = User.objects.create_user(
            username="hybrid_user_b",
            email="hybrid_b@hexmedia.local",
            password="PasswordB123"
        )
        self.tokens_a = generate_tokens_for_user(self.user_a)
        self.tokens_b = generate_tokens_for_user(self.user_b)

        # Create distinct projects for each user
        self.project_a = BookProject.objects.create(
            user=self.user_a,
            title="Project of User A"
        )
        self.project_b = BookProject.objects.create(
            user=self.user_b,
            title="Project of User B"
        )

    def test_case_1_neither_session_nor_bearer(self):
        res = self.client.get("/api/auth/me")
        self.assertEqual(res.status_code, 401)

        res_proj = self.client.get("/api/projects")
        self.assertEqual(res_proj.status_code, 401)

    def test_case_2_session_cookie_only(self):
        self.client.force_login(self.user_a)
        res = self.client.get("/api/auth/me")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["id"], self.user_a.id)

        # Verify projects returned are User A's
        res_proj = self.client.get("/api/projects")
        self.assertEqual(res_proj.status_code, 200)
        project_ids = [p["id"] for p in res_proj.json()]
        self.assertIn(str(self.project_a.id), project_ids)
        self.assertNotIn(str(self.project_b.id), project_ids)

    def test_case_3_bearer_jwt_only(self):
        # Client without session
        res = self.client.get(
            "/api/auth/me",
            HTTP_AUTHORIZATION=f"Bearer {self.tokens_b['access_token']}"
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["id"], self.user_b.id)

        # Verify projects returned are User B's
        res_proj = self.client.get(
            "/api/projects",
            HTTP_AUTHORIZATION=f"Bearer {self.tokens_b['access_token']}"
        )
        self.assertEqual(res_proj.status_code, 200)
        project_ids = [p["id"] for p in res_proj.json()]
        self.assertIn(str(self.project_b.id), project_ids)
        self.assertNotIn(str(self.project_a.id), project_ids)

    def test_case_4_both_present_and_matching(self):
        self.client.force_login(self.user_a)
        res = self.client.get(
            "/api/auth/me",
            HTTP_AUTHORIZATION=f"Bearer {self.tokens_a['access_token']}"
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["id"], self.user_a.id)

    def test_case_5_conflicting_session_user_a_and_bearer_user_b(self):
        """
        Adversarial test: Browser has active session cookie for User A,
        but API call sends Authorization: Bearer for User B.
        Bearer auth MUST take precedence, and response must reflect User B.
        User B must NOT see User A's data.
        """
        self.client.force_login(self.user_a)

        # /api/auth/me should return User B
        res = self.client.get(
            "/api/auth/me",
            HTTP_AUTHORIZATION=f"Bearer {self.tokens_b['access_token']}"
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["id"], self.user_b.id)
        self.assertEqual(res.json()["email"], self.user_b.email)

        # /api/projects should return User B's projects ONLY
        res_proj = self.client.get(
            "/api/projects",
            HTTP_AUTHORIZATION=f"Bearer {self.tokens_b['access_token']}"
        )
        self.assertEqual(res_proj.status_code, 200)
        project_ids = [p["id"] for p in res_proj.json()]
        self.assertIn(str(self.project_b.id), project_ids)
        self.assertNotIn(str(self.project_a.id), project_ids)

        # Direct access to User A's project should be 404
        res_single = self.client.get(
            f"/api/projects/{self.project_a.id}/chapters",
            HTTP_AUTHORIZATION=f"Bearer {self.tokens_b['access_token']}"
        )
        self.assertEqual(res_single.status_code, 404)

    def test_case_6_valid_session_with_invalid_bearer_token(self):
        """
        If a client has a valid session cookie but an invalid/expired Bearer token,
        JWTAuth returns None, and Django Ninja falls back to django_auth.
        """
        self.client.force_login(self.user_a)
        res = self.client.get(
            "/api/auth/me",
            HTTP_AUTHORIZATION="Bearer invalid.token.garbage"
        )
        # Because django_auth is in auth=[JWTAuth(), django_auth],
        # fallback to session succeeds
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["id"], self.user_a.id)


class DatabaseConstraintsAndIllegalAccessTests(TestCase):
    """
    Stress tests for database constraints and unowned record security:
    - Projects without users (orphaned) cannot be accessed or manipulated via API
    - Unowned chat messages cannot be read or leaked
    - Cascade deletion guarantees complete isolation
    """
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="db_tester",
            email="db_tester@hexmedia.local",
            password="SecurePassword123"
        )
        self.tokens = generate_tokens_for_user(self.user)
        self.auth_headers = {"HTTP_AUTHORIZATION": f"Bearer {self.tokens['access_token']}"}

        # Create an unowned/orphaned project (user=None)
        self.orphan_project = BookProject.objects.create(
            user=None,
            title="Orphan Project Without Owner",
            author="Unknown",
            status="DRAFT"
        )
        self.orphan_char = Character.objects.create(
            project=self.orphan_project,
            name="Ghost",
            assigned_voice="Fenrir"
        )
        self.orphan_chapter = Chapter.objects.create(
            project=self.orphan_project,
            number=1,
            title="Ghost Chapter"
        )
        self.orphan_scene = Scene.objects.create(
            project=self.orphan_project,
            chapter_obj=self.orphan_chapter,
            order=1,
            speaker=self.orphan_char,
            speaker_name="Ghost",
            raw_text="Orphan scene text"
        )

    def test_unowned_project_hidden_from_projects_list(self):
        res = self.client.get("/api/projects", **self.auth_headers)
        self.assertEqual(res.status_code, 200)
        project_ids = [p["id"] for p in res.json()]
        self.assertNotIn(str(self.orphan_project.id), project_ids)

    def test_unowned_project_endpoints_return_404(self):
        pid = str(self.orphan_project.id)
        # Chapters
        res = self.client.get(f"/api/projects/{pid}/chapters", **self.auth_headers)
        self.assertEqual(res.status_code, 404)

        # Timeline
        res = self.client.get(f"/api/projects/{pid}/timeline", **self.auth_headers)
        self.assertEqual(res.status_code, 404)

        # Live progress
        res = self.client.get(f"/api/projects/{pid}/live-progress", **self.auth_headers)
        self.assertEqual(res.status_code, 404)

        # Update characters
        res = self.client.post(
            f"/api/projects/{pid}/update-characters",
            data=json.dumps({"updates": []}),
            content_type="application/json",
            **self.auth_headers
        )
        self.assertEqual(res.status_code, 404)

        # Approve casting
        res = self.client.post(f"/api/projects/{pid}/approve-casting", **self.auth_headers)
        self.assertEqual(res.status_code, 404)

        # Execute chapter
        res = self.client.post(
            f"/api/projects/{pid}/execute-chapter",
            data=json.dumps({"chapter_number": 1}),
            content_type="application/json",
            **self.auth_headers
        )
        self.assertEqual(res.status_code, 404)

        # Export
        res = self.client.post(f"/api/projects/{pid}/export", **self.auth_headers)
        self.assertEqual(res.status_code, 404)

    def test_unowned_scene_endpoints_return_404(self):
        sid = str(self.orphan_scene.id)
        # Delete scene
        res_del = self.client.delete(f"/api/scenes/{sid}", **self.auth_headers)
        self.assertEqual(res_del.status_code, 404)

        # Regenerate scene
        res_reg = self.client.post(f"/api/scenes/{sid}/regenerate", **self.auth_headers)
        self.assertEqual(res_reg.status_code, 404)

        # Regenerate visual
        res_vis = self.client.post(f"/api/scenes/{sid}/regenerate-visual", **self.auth_headers)
        self.assertEqual(res_vis.status_code, 404)

    def test_chat_with_unowned_project_returns_404(self):
        res = self.client.post(
            "/api/chat",
            data=json.dumps({
                "prompt": "Try taking over orphan project",
                "project_id": str(self.orphan_project.id)
            }),
            content_type="application/json",
            **self.auth_headers
        )
        self.assertEqual(res.status_code, 404)

    def test_user_chat_messages_are_strictly_isolated(self):
        # Create user B
        user_b = User.objects.create_user(
            username="chat_user_b",
            email="chat_b@hexmedia.local",
            password="PasswordB123"
        )
        # User A has standalone message
        msg_a = ChatMessage.objects.create(
            user=self.user,
            project=None,
            role="USER",
            content="Secret prompt from user A"
        )
        # User B standalone message
        msg_b = ChatMessage.objects.create(
            user=user_b,
            project=None,
            role="USER",
            content="Prompt from user B"
        )

        # Query messages for user A
        qs_a = ChatMessage.objects.filter(project__isnull=True, user=self.user)
        self.assertIn(msg_a, qs_a)
        self.assertNotIn(msg_b, qs_a)

        # Query messages for user B
        qs_b = ChatMessage.objects.filter(project__isnull=True, user=user_b)
        self.assertIn(msg_b, qs_b)
        self.assertNotIn(msg_a, qs_b)

    def test_user_cascade_deletion_cleans_up_data(self):
        # Create user C with a project and messages
        user_c = User.objects.create_user(
            username="temp_user_c",
            email="temp_c@hexmedia.local",
            password="PasswordC123"
        )
        proj_c = BookProject.objects.create(user=user_c, title="Project C")
        msg_c = ChatMessage.objects.create(user=user_c, project=proj_c, content="Message C")

        user_c_id = user_c.id
        proj_c_id = proj_c.id
        msg_c_id = msg_c.id

        # Delete user C
        user_c.delete()

        # Project and message should be cascaded and deleted
        self.assertFalse(BookProject.objects.filter(id=proj_c_id).exists())
        self.assertFalse(ChatMessage.objects.filter(id=msg_c_id).exists())

        # Unowned project and user A's data must remain intact
        self.assertTrue(BookProject.objects.filter(id=self.orphan_project.id).exists())
