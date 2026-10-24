import json
import uuid
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.conf import settings
from .models import BookProject, Character, Chapter, Scene, TimelineState, ChatMessage
from .auth import (
    create_jwt_token,
    decode_jwt_payload,
    decode_jwt_token,
    generate_tokens_for_user,
    JWTAuth
)


class JWTAuthUtilityTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="jwt_tester",
            email="jwt_tester@hexmedia.local",
            password="securePassword123"
        )

    def test_jwt_creation_and_payload_decode(self):
        payload = {"user_id": self.user.id, "email": self.user.email, "role": "creator"}
        token = create_jwt_token(payload, expires_in_seconds=3600)
        self.assertIsInstance(token, str)
        self.assertEqual(len(token.split('.')), 3)

        decoded = decode_jwt_payload(token)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded.get("user_id"), self.user.id)
        self.assertEqual(decoded.get("email"), self.user.email)
        self.assertEqual(decoded.get("role"), "creator")

    def test_jwt_tampered_signature_rejected(self):
        token = create_jwt_token({"user_id": self.user.id}, expires_in_seconds=3600)
        parts = token.split('.')
        # Tamper payload
        tampered_token = f"{parts[0]}.eyAidXNlcl9pZCI6IDk5OSB9.{parts[2]}"
        self.assertIsNone(decode_jwt_payload(tampered_token))

        # Tamper signature
        tampered_sig = parts[2][:-4] + "xxxx"
        self.assertIsNone(decode_jwt_payload(f"{parts[0]}.{parts[1]}.{tampered_sig}"))

    def test_jwt_expired_token_rejected(self):
        # Create token that expired 10 seconds ago
        expired_token = create_jwt_token({"user_id": self.user.id}, expires_in_seconds=-10)
        self.assertIsNone(decode_jwt_payload(expired_token))
        self.assertIsNone(decode_jwt_token(expired_token))

    def test_decode_jwt_token_returns_user(self):
        tokens = generate_tokens_for_user(self.user)
        access_token = tokens["access_token"]
        user = decode_jwt_token(access_token)
        self.assertIsNotNone(user)
        self.assertEqual(user.id, self.user.id)
        self.assertEqual(user.username, self.user.username)

    def test_refresh_token_rejected_for_user_auth(self):
        tokens = generate_tokens_for_user(self.user)
        refresh_token = tokens["refresh_token"]
        # Refresh tokens must NOT authenticate API requests directly
        user = decode_jwt_token(refresh_token)
        self.assertIsNone(user)

    def test_inactive_user_rejected(self):
        self.user.is_active = False
        self.user.save()
        tokens = generate_tokens_for_user(self.user)
        user = decode_jwt_token(tokens["access_token"])
        self.assertIsNone(user)

    def test_generate_tokens_for_user_format(self):
        tokens = generate_tokens_for_user(self.user)
        self.assertIn("access_token", tokens)
        self.assertIn("refresh_token", tokens)
        self.assertIn("user", tokens)
        self.assertEqual(tokens["user"]["id"], self.user.id)
        self.assertEqual(tokens["user"]["username"], self.user.username)
        self.assertEqual(tokens["user"]["email"], self.user.email)


class AuthEndpointsTests(TestCase):
    def setUp(self):
        self.client = Client()
        self.existing_user = User.objects.create_user(
            username="existing_user",
            email="existing@hexmedia.local",
            password="Password123!"
        )

    def test_register_success_with_tokens_and_session(self):
        res = self.client.post(
            "/api/auth/register",
            data=json.dumps({
                "email": "newuser@hexmedia.local",
                "password": "ValidPassword123"
            }),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertIn("refresh_token", data)
        self.assertEqual(data["user"]["email"], "newuser@hexmedia.local")

        # Verify immediate session login
        me_res = self.client.get("/api/auth/me")
        self.assertEqual(me_res.status_code, 200)
        self.assertEqual(me_res.json()["email"], "newuser@hexmedia.local")

    def test_register_duplicate_email_fails(self):
        res = self.client.post(
            "/api/auth/register",
            data=json.dumps({
                "email": "existing@hexmedia.local",
                "password": "AnotherPassword123"
            }),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 400)
        self.assertIn("مسجل بالفعل", res.json()["detail"])

    def test_register_invalid_email_or_password_fails(self):
        # Invalid email
        res1 = self.client.post(
            "/api/auth/register",
            data=json.dumps({"email": "notanemail", "password": "Password123"}),
            content_type="application/json"
        )
        self.assertEqual(res1.status_code, 400)

        # Short password
        res2 = self.client.post(
            "/api/auth/register",
            data=json.dumps({"email": "shortpass@hexmedia.local", "password": "123"}),
            content_type="application/json"
        )
        self.assertEqual(res2.status_code, 400)

    def test_login_success_with_email_and_password(self):
        res = self.client.post(
            "/api/auth/login",
            data=json.dumps({
                "email": "existing@hexmedia.local",
                "password": "Password123!"
            }),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["id"], self.existing_user.id)

    def test_login_success_with_username_and_password(self):
        res = self.client.post(
            "/api/auth/login",
            data=json.dumps({
                "username": "existing_user",
                "password": "Password123!"
            }),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["username"], "existing_user")

    def test_login_wrong_password_returns_401(self):
        res = self.client.post(
            "/api/auth/login",
            data=json.dumps({
                "email": "existing@hexmedia.local",
                "password": "WrongPassword!"
            }),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 401)
        self.assertEqual(res.json()["detail"], "بيانات الدخول غير صحيحة")

    def test_login_nonexistent_user_returns_401(self):
        res = self.client.post(
            "/api/auth/login",
            data=json.dumps({
                "email": "nobody@hexmedia.local",
                "password": "Password123!"
            }),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 401)

    def test_refresh_token_success(self):
        tokens = generate_tokens_for_user(self.existing_user)
        res = self.client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh_token": tokens["refresh_token"]}),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("access_token", data)
        self.assertEqual(data["user"]["id"], self.existing_user.id)

    def test_refresh_token_rejects_access_token(self):
        tokens = generate_tokens_for_user(self.existing_user)
        # Using access token where refresh token is required must fail with 401
        res = self.client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh_token": tokens["access_token"]}),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 401)

    def test_refresh_token_invalid_fails(self):
        res = self.client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh_token": "invalid.garbage.token"}),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 401)

    def test_auth_me_authenticated_bearer(self):
        tokens = generate_tokens_for_user(self.existing_user)
        res = self.client.get(
            "/api/auth/me",
            HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}"
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["id"], self.existing_user.id)
        self.assertEqual(res.json()["email"], self.existing_user.email)

    def test_auth_me_authenticated_session(self):
        self.client.force_login(self.existing_user)
        res = self.client.get("/api/auth/me")
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["id"], self.existing_user.id)

    def test_auth_me_anonymous_returns_401(self):
        res = self.client.get("/api/auth/me")
        self.assertEqual(res.status_code, 401)

    def test_logout_endpoint(self):
        self.client.force_login(self.existing_user)
        res = self.client.post("/api/auth/logout")
        self.assertEqual(res.status_code, 200)
        self.assertTrue(res.json()["success"])

        # Session should now be cleared
        me_res = self.client.get("/api/auth/me")
        self.assertEqual(me_res.status_code, 401)


class AnonymousAccessGateTests(TestCase):
    def setUp(self):
        self.client = Client()

    def test_anonymous_health_check_permitted(self):
        res = self.client.get("/api/health")
        self.assertEqual(res.status_code, 200)

    def test_anonymous_config_returns_401(self):
        res1 = self.client.get("/api/config")
        self.assertEqual(res1.status_code, 401)

        res2 = self.client.post(
            "/api/config",
            data=json.dumps({"llm_model": "test"}),
            content_type="application/json"
        )
        self.assertEqual(res2.status_code, 401)

    def test_anonymous_chat_returns_401(self):
        res = self.client.post(
            "/api/chat",
            data=json.dumps({"prompt": "Hello"}),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 401)

    def test_anonymous_projects_list_returns_401(self):
        res = self.client.get("/api/projects")
        self.assertEqual(res.status_code, 401)

    def test_anonymous_project_chapters_returns_401(self):
        fake_id = str(uuid.uuid4())
        res = self.client.get(f"/api/projects/{fake_id}/chapters")
        self.assertEqual(res.status_code, 401)

    def test_anonymous_scene_regenerate_returns_401(self):
        fake_id = str(uuid.uuid4())
        res = self.client.post(f"/api/scenes/{fake_id}/regenerate")
        self.assertEqual(res.status_code, 401)

    def test_anonymous_scene_delete_returns_401(self):
        fake_id = str(uuid.uuid4())
        res = self.client.delete(f"/api/scenes/{fake_id}")
        self.assertEqual(res.status_code, 401)


class MultiTenantIsolationTests(TestCase):
    def setUp(self):
        self.client_a = Client()
        self.client_b = Client()

        self.user_a = User.objects.create_user(
            username="tenant_a",
            email="tenant_a@hexmedia.local",
            password="PasswordA123"
        )
        self.user_b = User.objects.create_user(
            username="tenant_b",
            email="tenant_b@hexmedia.local",
            password="PasswordB123"
        )

        self.tokens_a = generate_tokens_for_user(self.user_a)
        self.tokens_b = generate_tokens_for_user(self.user_b)

        self.header_a = {"HTTP_AUTHORIZATION": f"Bearer {self.tokens_a['access_token']}"}
        self.header_b = {"HTTP_AUTHORIZATION": f"Bearer {self.tokens_b['access_token']}"}

        # User A creates a project and related models
        self.project_a = BookProject.objects.create(
            user=self.user_a,
            title="User A Epic Novel",
            author="Author A",
            status="READY",
            narration_mode="SMART"
        )
        self.char_a = Character.objects.create(
            project=self.project_a,
            name="Hero A",
            assigned_voice="Fenrir",
            role_type="PROTAGONIST"
        )
        self.chapter_a = Chapter.objects.create(
            project=self.project_a,
            number=1,
            title="Chapter 1"
        )
        self.scene_a = Scene.objects.create(
            project=self.project_a,
            chapter_obj=self.chapter_a,
            order=1,
            speaker=self.char_a,
            speaker_name="Hero A",
            raw_text="Hello from user A",
            duration_seconds=3.0,
            status="GENERATED"
        )
        self.timeline_a = TimelineState.objects.create(
            project=self.project_a,
            designcombo_json={"tracks": []},
            total_duration=3.0
        )

        # User B creates their own project
        self.project_b = BookProject.objects.create(
            user=self.user_b,
            title="User B Story",
            author="Author B"
        )

    def test_user_b_cannot_view_user_a_project_chapters(self):
        res = self.client_b.get(
            f"/api/projects/{self.project_a.id}/chapters",
            **self.header_b
        )
        self.assertEqual(res.status_code, 404)

    def test_user_b_cannot_view_user_a_project_timeline(self):
        res = self.client_b.get(
            f"/api/projects/{self.project_a.id}/timeline",
            **self.header_b
        )
        self.assertEqual(res.status_code, 404)

    def test_user_b_cannot_view_user_a_project_live_progress(self):
        res = self.client_b.get(
            f"/api/projects/{self.project_a.id}/live-progress",
            **self.header_b
        )
        self.assertEqual(res.status_code, 404)

    def test_user_b_cannot_update_characters_in_user_a_project(self):
        res = self.client_b.post(
            f"/api/projects/{self.project_a.id}/update-characters",
            data=json.dumps({"updates": [{"character_id": str(self.char_a.id), "assigned_voice": "Kore"}]}),
            content_type="application/json",
            **self.header_b
        )
        self.assertEqual(res.status_code, 404)

    def test_user_b_cannot_approve_casting_in_user_a_project(self):
        res = self.client_b.post(
            f"/api/projects/{self.project_a.id}/approve-casting",
            **self.header_b
        )
        self.assertEqual(res.status_code, 404)

    def test_user_b_cannot_execute_chapter_in_user_a_project(self):
        res = self.client_b.post(
            f"/api/projects/{self.project_a.id}/execute-chapter",
            data=json.dumps({"chapter_number": 1}),
            content_type="application/json",
            **self.header_b
        )
        self.assertEqual(res.status_code, 404)

    def test_user_b_cannot_export_user_a_project(self):
        res = self.client_b.post(
            f"/api/projects/{self.project_a.id}/export",
            **self.header_b
        )
        self.assertEqual(res.status_code, 404)

    def test_user_b_cannot_start_continuous_in_user_a_project(self):
        res = self.client_b.post(
            f"/api/projects/{self.project_a.id}/start-continuous",
            data=json.dumps({"target_duration_minutes": 5}),
            content_type="application/json",
            **self.header_b
        )
        self.assertEqual(res.status_code, 404)

    def test_user_b_cannot_pause_continuous_in_user_a_project(self):
        res = self.client_b.post(
            f"/api/projects/{self.project_a.id}/pause-continuous",
            **self.header_b
        )
        self.assertEqual(res.status_code, 404)

    def test_user_b_cannot_resume_continuous_in_user_a_project(self):
        res = self.client_b.post(
            f"/api/projects/{self.project_a.id}/resume-continuous",
            **self.header_b
        )
        self.assertEqual(res.status_code, 404)

    def test_user_b_cannot_set_narration_mode_in_user_a_project(self):
        res = self.client_b.post(
            f"/api/projects/{self.project_a.id}/set-narration-mode",
            data=json.dumps({"narration_mode": "FULL"}),
            content_type="application/json",
            **self.header_b
        )
        self.assertEqual(res.status_code, 404)

    def test_user_b_cannot_delete_user_a_scene(self):
        res = self.client_b.delete(
            f"/api/scenes/{self.scene_a.id}",
            **self.header_b
        )
        self.assertEqual(res.status_code, 404)
        # Verify scene still exists
        self.assertTrue(Scene.objects.filter(id=self.scene_a.id).exists())

    def test_user_b_cannot_regenerate_user_a_scene(self):
        res = self.client_b.post(
            f"/api/scenes/{self.scene_a.id}/regenerate",
            **self.header_b
        )
        self.assertEqual(res.status_code, 404)

    def test_user_b_cannot_regenerate_visual_user_a_scene(self):
        res = self.client_b.post(
            f"/api/scenes/{self.scene_a.id}/regenerate-visual",
            **self.header_b
        )
        self.assertEqual(res.status_code, 404)

    def test_user_b_cannot_chat_with_user_a_project_id(self):
        res = self.client_b.post(
            "/api/chat",
            data=json.dumps({
                "prompt": "Tamper attempt",
                "project_id": str(self.project_a.id)
            }),
            content_type="application/json",
            **self.header_b
        )
        self.assertEqual(res.status_code, 404)

    def test_user_a_can_access_own_project_and_scenes(self):
        res_ch = self.client_a.get(
            f"/api/projects/{self.project_a.id}/chapters",
            **self.header_a
        )
        self.assertEqual(res_ch.status_code, 200)
        self.assertEqual(res_ch.json()["chapters_count"], 1)

        res_tl = self.client_a.get(
            f"/api/projects/{self.project_a.id}/timeline",
            **self.header_a
        )
        self.assertEqual(res_tl.status_code, 200)
        self.assertEqual(res_tl.json()["project"]["title"], "User A Epic Novel")

    def test_projects_endpoint_only_lists_authenticated_user_projects(self):
        # User A query
        res_a = self.client_a.get("/api/projects", **self.header_a)
        self.assertEqual(res_a.status_code, 200)
        p_ids_a = [p["id"] for p in res_a.json()]
        self.assertIn(str(self.project_a.id), p_ids_a)
        self.assertNotIn(str(self.project_b.id), p_ids_a)

        # User B query
        res_b = self.client_b.get("/api/projects", **self.header_b)
        self.assertEqual(res_b.status_code, 200)
        p_ids_b = [p["id"] for p in res_b.json()]
        self.assertIn(str(self.project_b.id), p_ids_b)
        self.assertNotIn(str(self.project_a.id), p_ids_b)


class DataMigrationBackfillTests(TestCase):
    def test_existing_projects_have_owner_or_admin_assigned(self):
        # All projects in database must have user assigned
        unowned_count = BookProject.objects.filter(user__isnull=True).count()
        self.assertEqual(unowned_count, 0)
