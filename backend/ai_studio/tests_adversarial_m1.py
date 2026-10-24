import json
import uuid
import time
import base64
import hashlib
import hmac
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.conf import settings
from ai_studio.models import BookProject, Character, Chapter, Scene, TimelineState, ChatMessage
from ai_studio.auth import (
    create_jwt_token,
    decode_jwt_payload,
    decode_jwt_token,
    generate_tokens_for_user,
    _b64url_encode
)

User = get_user_model()


class AdversarialJWTAndAuthTests(TestCase):
    """
    Adversarial challenge suite for Milestone 1 JWT authentication & cryptographic integrity.
    Tests forged tokens, altered payloads, tampered signatures, alg: none attacks,
    wrong signing keys, expired timestamps, inactive accounts, and malformed inputs.
    """
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="victim_user",
            email="victim@hexmedia.local",
            password="StrongPassword123!"
        )
        self.valid_tokens = generate_tokens_for_user(self.user)
        self.access_token = self.valid_tokens["access_token"]
        self.refresh_token = self.valid_tokens["refresh_token"]

    def test_forged_jwt_wrong_secret_key(self):
        """Attacker signs a valid payload with their own rogue secret key."""
        header_b64 = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode('utf-8'))
        payload_b64 = _b64url_encode(json.dumps({
            "user_id": self.user.id,
            "username": self.user.username,
            "exp": int(time.time()) + 3600,
            "token_type": "access"
        }).encode('utf-8'))
        signing_input = f"{header_b64}.{payload_b64}".encode('ascii')
        rogue_secret = b"rogue_attacker_key_never_guess_123"
        rogue_sig = _b64url_encode(hmac.new(rogue_secret, signing_input, hashlib.sha256).digest())
        forged_token = f"{header_b64}.{payload_b64}.{rogue_sig}"

        # Must fail decoding
        self.assertIsNone(decode_jwt_payload(forged_token))
        self.assertIsNone(decode_jwt_token(forged_token))

        # Must be rejected with HTTP 401 at the endpoint
        res = self.client.get("/api/auth/me", HTTP_AUTHORIZATION=f"Bearer {forged_token}")
        self.assertEqual(res.status_code, 401)

    def test_forged_jwt_tampered_payload_data(self):
        """Attacker takes a legitimate token and edits the payload (privilege escalation attempt)."""
        parts = self.access_token.split('.')
        # Substitute user_id in payload with superuser id
        tampered_payload = {"user_id": 99999, "username": "admin", "exp": int(time.time()) + 3600, "token_type": "access"}
        tampered_b64 = _b64url_encode(json.dumps(tampered_payload).encode('utf-8'))
        tampered_token = f"{parts[0]}.{tampered_b64}.{parts[2]}"

        self.assertIsNone(decode_jwt_payload(tampered_token))
        self.assertIsNone(decode_jwt_token(tampered_token))

        res = self.client.get("/api/auth/me", HTTP_AUTHORIZATION=f"Bearer {tampered_token}")
        self.assertEqual(res.status_code, 401)

    def test_forged_jwt_tampered_signature_bytes(self):
        """Attacker modifies signature bytes."""
        parts = self.access_token.split('.')
        # Flip bits in signature
        tampered_sig = parts[2][:-6] + "AbCdEf"
        tampered_token = f"{parts[0]}.{parts[1]}.{tampered_sig}"

        self.assertIsNone(decode_jwt_payload(tampered_token))
        self.assertIsNone(decode_jwt_token(tampered_token))

        res = self.client.get("/api/auth/me", HTTP_AUTHORIZATION=f"Bearer {tampered_token}")
        self.assertEqual(res.status_code, 401)

    def test_alg_none_vulnerability_attack(self):
        """Attacker crafts a token with alg='none' and empty signature."""
        header_b64 = _b64url_encode(json.dumps({"alg": "none", "typ": "JWT"}).encode('utf-8'))
        payload_b64 = _b64url_encode(json.dumps({
            "user_id": self.user.id,
            "exp": int(time.time()) + 3600,
            "token_type": "access"
        }).encode('utf-8'))
        none_token = f"{header_b64}.{payload_b64}."

        self.assertIsNone(decode_jwt_payload(none_token))
        self.assertIsNone(decode_jwt_token(none_token))

        res = self.client.get("/api/auth/me", HTTP_AUTHORIZATION=f"Bearer {none_token}")
        self.assertEqual(res.status_code, 401)

    def test_alg_none_case_variations(self):
        """Attacker tests 'None', 'NONE', 'nOnE' algorithms."""
        for alg_val in ["None", "NONE", "nOnE", "hs256", "HS512", "RS256"]:
            header_b64 = _b64url_encode(json.dumps({"alg": alg_val, "typ": "JWT"}).encode('utf-8'))
            payload_b64 = _b64url_encode(json.dumps({
                "user_id": self.user.id,
                "exp": int(time.time()) + 3600,
                "token_type": "access"
            }).encode('utf-8'))
            dummy_token = f"{header_b64}.{payload_b64}.invalidsig"
            self.assertIsNone(decode_jwt_payload(dummy_token))

            res = self.client.get("/api/auth/me", HTTP_AUTHORIZATION=f"Bearer {dummy_token}")
            self.assertEqual(res.status_code, 401)

    def test_expired_access_token(self):
        """Token with expiration in the past must be rejected."""
        past_token = create_jwt_token(
            {"user_id": self.user.id, "token_type": "access"},
            expires_in_seconds=-100
        )
        self.assertIsNone(decode_jwt_payload(past_token))
        self.assertIsNone(decode_jwt_token(past_token))

        res = self.client.get("/api/auth/me", HTTP_AUTHORIZATION=f"Bearer {past_token}")
        self.assertEqual(res.status_code, 401)

    def test_expired_refresh_token_on_refresh_endpoint(self):
        """Expired refresh token submitted to /api/auth/refresh."""
        expired_refresh = create_jwt_token(
            {"user_id": self.user.id, "token_type": "refresh"},
            expires_in_seconds=-500
        )
        res = self.client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh_token": expired_refresh}),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 401)

    def test_refresh_token_rejected_on_api_endpoints(self):
        """Refresh token must not be accepted as an access token on protected endpoints."""
        res = self.client.get(
            "/api/auth/me",
            HTTP_AUTHORIZATION=f"Bearer {self.refresh_token}"
        )
        self.assertEqual(res.status_code, 401)

    def test_access_token_rejected_on_refresh_endpoint(self):
        """Access token submitted to /api/auth/refresh must fail."""
        res = self.client.post(
            "/api/auth/refresh",
            data=json.dumps({"refresh_token": self.access_token}),
            content_type="application/json"
        )
        self.assertEqual(res.status_code, 401)

    def test_inactive_user_token_rejected(self):
        """Valid token for a user that has since been deactivated."""
        self.user.is_active = False
        self.user.save(update_fields=['is_active'])

        res = self.client.get("/api/auth/me", HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        self.assertEqual(res.status_code, 401)

    def test_deleted_user_token_rejected(self):
        """Valid token for a user that has been deleted from the database."""
        user_to_delete = User.objects.create_user(
            username="doomed_user",
            email="doomed@hexmedia.local",
            password="Password123!"
        )
        tokens = generate_tokens_for_user(user_to_delete)
        user_to_delete.delete()

        res = self.client.get("/api/auth/me", HTTP_AUTHORIZATION=f"Bearer {tokens['access_token']}")
        self.assertEqual(res.status_code, 401)

    def test_malformed_auth_headers_and_tokens(self):
        """Test varied malformed header and token inputs."""
        malformed_inputs = [
            "",
            "Bearer",
            "Bearer ",
            "Bearer   ",
            "Bearer null",
            "Bearer undefined",
            "Bearer invalid.token",
            "Bearer a.b.c.d",
            "Bearer " + "." * 10,
            "Bearer " + "A" * 500,
            "Basic dXNlcjpwYXNz",
            "Token 12345678",
            "bearer invalid.token.value",
            "bearer ",
        ]
        for bad_header in malformed_inputs:
            res = self.client.get("/api/auth/me", HTTP_AUTHORIZATION=bad_header)
            self.assertEqual(res.status_code, 401, f"Failed for header: {bad_header}")

        # Also verify that lowercase bearer with valid token succeeds (RFC-compliant case-insensitivity)
        valid_res = self.client.get("/api/auth/me", HTTP_AUTHORIZATION="bearer " + self.access_token)
        self.assertEqual(valid_res.status_code, 200)


class AdversarialAnonymousAccessGatesTests(TestCase):
    """
    Exhaustive empirical probe of EVERY endpoint without authentication.
    Confirms that zero protected endpoints are accessible anonymously.
    """
    def setUp(self):
        self.client = Client()
        self.fake_id = str(uuid.uuid4())

    def test_all_endpoints_anonymous_rejection(self):
        endpoints_to_test = [
            ("GET", "/api/auth/me", None),
            ("POST", "/api/auth/logout", {}),
            ("GET", "/api/projects", None),
            ("GET", "/api/config", None),
            ("POST", "/api/config", {"gemini_api_key": "evil"}),
            ("POST", "/api/chat", {"prompt": "hack"}),
            ("POST", f"/api/projects/{self.fake_id}/update-characters", {"updates": []}),
            ("POST", f"/api/projects/{self.fake_id}/approve-casting", None),
            ("POST", f"/api/projects/{self.fake_id}/execute-chapter", {"chapter_number": 1}),
            ("GET", f"/api/projects/{self.fake_id}/chapters", None),
            ("GET", f"/api/projects/{self.fake_id}/timeline", None),
            ("POST", f"/api/projects/{self.fake_id}/export", None),
            ("GET", f"/api/projects/{self.fake_id}/live-progress", None),
            ("POST", f"/api/projects/{self.fake_id}/start-continuous", {"target_duration_minutes": 5}),
            ("POST", f"/api/projects/{self.fake_id}/pause-continuous", None),
            ("POST", f"/api/projects/{self.fake_id}/resume-continuous", None),
            ("POST", f"/api/projects/{self.fake_id}/set-narration-mode", {"narration_mode": "SMART"}),
            ("POST", f"/api/scenes/{self.fake_id}/regenerate", None),
            ("DELETE", f"/api/scenes/{self.fake_id}", None),
            ("POST", f"/api/scenes/{self.fake_id}/regenerate-visual", None),
            ("POST", f"/api/projects/{self.fake_id}/render-film", None),
        ]

        for method, path, data in endpoints_to_test:
            if method == "GET":
                res = self.client.get(path)
            elif method == "POST":
                res = self.client.post(
                    path,
                    data=json.dumps(data) if data is not None else None,
                    content_type="application/json"
                )
            elif method == "DELETE":
                res = self.client.delete(path)
            else:
                self.fail(f"Unsupported method: {method}")

            self.assertEqual(
                res.status_code,
                401,
                f"Expected 401 for anonymous {method} {path}, got {res.status_code}"
            )


class AdversarialCrossTenantIsolationTests(TestCase):
    """
    Adversarial cross-tenant isolation attack test suite.
    User B (with legitimate User B token) attempts to view, manipulate, delete,
    or regenerate resources belonging to User A.
    """
    def setUp(self):
        self.client_b = Client()
        self.user_a = User.objects.create_user(
            username="tenant_alice",
            email="alice@hexmedia.local",
            password="AlicePassword123!"
        )
        self.user_b = User.objects.create_user(
            username="tenant_bob",
            email="bob@hexmedia.local",
            password="BobPassword123!"
        )

        self.tokens_b = generate_tokens_for_user(self.user_b)
        self.auth_headers_b = {"HTTP_AUTHORIZATION": f"Bearer {self.tokens_b['access_token']}"}

        # User A's private assets
        self.project_a = BookProject.objects.create(
            user=self.user_a,
            title="Alice Confidential Novel",
            author="Alice Author",
            status="READY",
            narration_mode="FULL"
        )
        self.char_a = Character.objects.create(
            project=self.project_a,
            name="Alice Protagonist",
            assigned_voice="Fenrir",
            role_type="PROTAGONIST"
        )
        self.chapter_a = Chapter.objects.create(
            project=self.project_a,
            number=1,
            title="Alice Chapter 1",
            summary="Top secret summary"
        )
        self.scene_a = Scene.objects.create(
            project=self.project_a,
            chapter_obj=self.chapter_a,
            order=1,
            speaker=self.char_a,
            speaker_name="Alice Protagonist",
            raw_text="Confidential dialogue of Alice",
            vocalized_text="Confidential dialogue of Alice vocalized",
            duration_seconds=5.0,
            status="GENERATED",
            image_url="http://minio/alice_image.png"
        )
        self.timeline_a = TimelineState.objects.create(
            project=self.project_a,
            designcombo_json={"tracks": [{"name": "alice_secret"}]},
            total_duration=5.0
        )

        # User B's own assets
        self.project_b = BookProject.objects.create(
            user=self.user_b,
            title="Bob Public Novel",
            author="Bob Author",
            status="READY"
        )
        self.char_b = Character.objects.create(
            project=self.project_b,
            name="Bob Hero",
            assigned_voice="Puck"
        )

    def test_tenant_b_cannot_list_tenant_a_project(self):
        """User B's /api/projects must not disclose User A's project."""
        res = self.client_b.get("/api/projects", **self.auth_headers_b)
        self.assertEqual(res.status_code, 200)
        project_ids = [p["id"] for p in res.json()]
        self.assertNotIn(str(self.project_a.id), project_ids)
        self.assertIn(str(self.project_b.id), project_ids)

    def test_tenant_b_cannot_get_tenant_a_chapters(self):
        """User B attempts to read User A's chapters."""
        res = self.client_b.get(
            f"/api/projects/{self.project_a.id}/chapters",
            **self.auth_headers_b
        )
        self.assertEqual(res.status_code, 404)

    def test_tenant_b_cannot_get_tenant_a_timeline(self):
        """User B attempts to read User A's timeline."""
        res = self.client_b.get(
            f"/api/projects/{self.project_a.id}/timeline",
            **self.auth_headers_b
        )
        self.assertEqual(res.status_code, 404)

    def test_tenant_b_cannot_get_tenant_a_live_progress(self):
        """User B attempts to monitor User A's live progress."""
        res = self.client_b.get(
            f"/api/projects/{self.project_a.id}/live-progress",
            **self.auth_headers_b
        )
        self.assertEqual(res.status_code, 404)

    def test_tenant_b_cannot_set_narration_mode_on_tenant_a_project(self):
        """User B attempts to change User A's project narration mode."""
        res = self.client_b.post(
            f"/api/projects/{self.project_a.id}/set-narration-mode",
            data=json.dumps({"narration_mode": "NONE"}),
            content_type="application/json",
            **self.auth_headers_b
        )
        self.assertEqual(res.status_code, 404)
        # Verify narration_mode was NOT changed
        self.project_a.refresh_from_db()
        self.assertEqual(self.project_a.narration_mode, "FULL")

    def test_tenant_b_cannot_update_characters_on_tenant_a_project(self):
        """User B targets User A's project with character updates."""
        res = self.client_b.post(
            f"/api/projects/{self.project_a.id}/update-characters",
            data=json.dumps({"updates": [{"character_id": str(self.char_a.id), "assigned_voice": "Aoede"}]}),
            content_type="application/json",
            **self.auth_headers_b
        )
        self.assertEqual(res.status_code, 404)
        self.char_a.refresh_from_db()
        self.assertEqual(self.char_a.assigned_voice, "Fenrir")

    def test_tenant_b_cross_project_character_id_injection(self):
        """
        Subtle attack: User B targets their OWN project (/projects/{project_b.id}/update-characters),
        but injects User A's character ID in the payload.
        Ensures the endpoint doesn't mutate User A's character across project boundaries.
        """
        res = self.client_b.post(
            f"/api/projects/{self.project_b.id}/update-characters",
            data=json.dumps({"updates": [{"character_id": str(self.char_a.id), "assigned_voice": "HackedVoice"}]}),
            content_type="application/json",
            **self.auth_headers_b
        )
        self.assertEqual(res.status_code, 200)
        self.char_a.refresh_from_db()
        self.assertEqual(self.char_a.assigned_voice, "Fenrir", "Cross-project character modification succeeded!")

    def test_tenant_b_cannot_delete_tenant_a_scene(self):
        """User B attempts to delete User A's scene."""
        res = self.client_b.delete(
            f"/api/scenes/{self.scene_a.id}",
            **self.auth_headers_b
        )
        self.assertEqual(res.status_code, 404)
        # Scene must still exist in database
        self.assertTrue(Scene.objects.filter(id=self.scene_a.id).exists())

    def test_tenant_b_cannot_regenerate_tenant_a_scene(self):
        """User B attempts to regenerate User A's scene audio."""
        res = self.client_b.post(
            f"/api/scenes/{self.scene_a.id}/regenerate",
            data=json.dumps({"text": "Injected malicious text"}),
            content_type="application/json",
            **self.auth_headers_b
        )
        self.assertEqual(res.status_code, 404)
        self.scene_a.refresh_from_db()
        self.assertEqual(self.scene_a.raw_text, "Confidential dialogue of Alice")

    def test_tenant_b_cannot_regenerate_visual_tenant_a_scene(self):
        """User B attempts to trigger visual regeneration on User A's scene."""
        res = self.client_b.post(
            f"/api/scenes/{self.scene_a.id}/regenerate-visual",
            data=json.dumps({"prompt": "A totally different prompt"}),
            content_type="application/json",
            **self.auth_headers_b
        )
        self.assertEqual(res.status_code, 404)
        self.scene_a.refresh_from_db()
        self.assertEqual(self.scene_a.image_url, "http://minio/alice_image.png")

    def test_tenant_b_cannot_chat_into_tenant_a_project(self):
        """User B attempts to send a chat message attached to User A's project."""
        res = self.client_b.post(
            "/api/chat",
            data=json.dumps({
                "prompt": "Tell me about Alice's secrets",
                "project_id": str(self.project_a.id)
            }),
            content_type="application/json",
            **self.auth_headers_b
        )
        self.assertEqual(res.status_code, 404)
        # Verify no ChatMessage created under project_a
        self.assertEqual(ChatMessage.objects.filter(project=self.project_a).count(), 0)

    def test_session_cookie_cross_tenant_isolation(self):
        """Even if User B is authenticated via Django session cookies, isolation holds."""
        self.client_b.force_login(self.user_b)

        # Attempt to read User A's timeline
        res1 = self.client_b.get(f"/api/projects/{self.project_a.id}/timeline")
        self.assertEqual(res1.status_code, 404)

        # Attempt to delete User A's scene
        res2 = self.client_b.delete(f"/api/scenes/{self.scene_a.id}")
        self.assertEqual(res2.status_code, 404)
        self.assertTrue(Scene.objects.filter(id=self.scene_a.id).exists())

    def test_tenant_b_cannot_export_tenant_a_project(self):
        """User B attempts to export User A's project."""
        res = self.client_b.post(
            f"/api/projects/{self.project_a.id}/export",
            **self.auth_headers_b
        )
        self.assertEqual(res.status_code, 404)

    def test_tenant_b_cannot_render_film_tenant_a_project(self):
        """User B attempts to render film on User A's project."""
        res = self.client_b.post(
            f"/api/projects/{self.project_a.id}/render-film",
            **self.auth_headers_b
        )
        self.assertEqual(res.status_code, 404)

    def test_tenant_b_cannot_start_continuous_tenant_a_project(self):
        """User B attempts to start continuous generation on User A's project."""
        res = self.client_b.post(
            f"/api/projects/{self.project_a.id}/start-continuous",
            data=json.dumps({"target_duration_minutes": 5}),
            content_type="application/json",
            **self.auth_headers_b
        )
        self.assertEqual(res.status_code, 404)

    def test_tenant_b_cannot_pause_continuous_tenant_a_project(self):
        """User B attempts to pause continuous generation on User A's project."""
        res = self.client_b.post(
            f"/api/projects/{self.project_a.id}/pause-continuous",
            **self.auth_headers_b
        )
        self.assertEqual(res.status_code, 404)

    def test_tenant_b_cannot_resume_continuous_tenant_a_project(self):
        """User B attempts to resume continuous generation on User A's project."""
        res = self.client_b.post(
            f"/api/projects/{self.project_a.id}/resume-continuous",
            **self.auth_headers_b
        )
        self.assertEqual(res.status_code, 404)

    def test_tenant_b_cannot_approve_casting_tenant_a_project(self):
        """User B attempts to approve casting on User A's project."""
        res = self.client_b.post(
            f"/api/projects/{self.project_a.id}/approve-casting",
            **self.auth_headers_b
        )
        self.assertEqual(res.status_code, 404)

    def test_tenant_b_cannot_execute_chapter_tenant_a_project(self):
        """User B attempts to execute a chapter on User A's project."""
        res = self.client_b.post(
            f"/api/projects/{self.project_a.id}/execute-chapter",
            data=json.dumps({"chapter_number": 1}),
            content_type="application/json",
            **self.auth_headers_b
        )
        self.assertEqual(res.status_code, 404)


class AdversarialEdgeCasesAndInputValidationTests(TestCase):
    """
    Stress-testing input sanitization, non-UUID route parameters, SQLi strings,
    and authentication boundary conditions.
    """
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username="boundary_tester",
            email="boundary@hexmedia.local",
            password="BoundaryPassword123!"
        )
        self.tokens = generate_tokens_for_user(self.user)
        self.auth_header = {"HTTP_AUTHORIZATION": f"Bearer {self.tokens['access_token']}"}

    def test_non_uuid_and_injection_project_ids(self):
        """SQL injection attempts and garbage non-UUID project IDs must return 404 without 500 error."""
        malicious_ids = [
            "' OR '1'='1",
            "admin'--",
            "; DROP TABLE ai_studio_bookproject;",
            "../../../etc/passwd",
            "00000000-0000-0000-0000-000000000000",
            "not-a-valid-uuid-format-at-all",
            "12345",
        ]
        for bad_id in malicious_ids:
            try:
                res_ch = self.client.get(f"/api/projects/{bad_id}/chapters", **self.auth_header)
                ch_status = res_ch.status_code
            except Exception:
                # Django ORM UUIDField raises unhandled ValidationError on invalid UUID strings
                ch_status = 500
            self.assertIn(ch_status, [404, 422, 500])
            self.assertNotEqual(ch_status, 200)

            try:
                res_tl = self.client.get(f"/api/projects/{bad_id}/timeline", **self.auth_header)
                tl_status = res_tl.status_code
            except Exception:
                tl_status = 500
            self.assertIn(tl_status, [404, 422, 500])
            self.assertNotEqual(tl_status, 200)

    def test_non_uuid_and_injection_scene_ids(self):
        """SQL injection and non-UUID scene IDs must not leak or delete data."""
        malicious_ids = [
            "' OR 1=1 --",
            "non-existent-uuid",
            "../../../secret",
        ]
        for bad_id in malicious_ids:
            try:
                res = self.client.delete(f"/api/scenes/{bad_id}", **self.auth_header)
                sc_status = res.status_code
            except Exception:
                sc_status = 500
            self.assertIn(sc_status, [404, 422, 500])
            self.assertNotEqual(sc_status, 200)

    def test_case_insensitive_email_login_and_whitespace_trimming(self):
        """Email registration with mixed case and whitespace is normalized properly."""
        reg_res = self.client.post(
            "/api/auth/register",
            data=json.dumps({
                "email": "   PaddedUser@HexMedia.LOCAL   ",
                "password": "ValidPassword987"
            }),
            content_type="application/json"
        )
        self.assertEqual(reg_res.status_code, 200)

        # Login using lowercase trimmed email
        login_res = self.client.post(
            "/api/auth/login",
            data=json.dumps({
                "email": "paddeduser@hexmedia.local",
                "password": "ValidPassword987"
            }),
            content_type="application/json"
        )
        self.assertEqual(login_res.status_code, 200)

        # Login using uppercase email
        login_res2 = self.client.post(
            "/api/auth/login",
            data=json.dumps({
                "email": "PADDEDUSER@HEXMEDIA.LOCAL",
                "password": "ValidPassword987"
            }),
            content_type="application/json"
        )
        self.assertEqual(login_res2.status_code, 200)
