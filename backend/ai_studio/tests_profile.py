import json
import uuid
from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import BookProject, Scene, Character
from .auth import generate_tokens_for_user


class ProfileAndProjectsAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(
            username="profile_user_a",
            email="user_a@hexmedia.local",
            password="Password123!"
        )
        self.user_b = User.objects.create_user(
            username="profile_user_b",
            email="user_b@hexmedia.local",
            password="Password123!"
        )

        tokens_a = generate_tokens_for_user(self.user_a)
        self.token_a = tokens_a["access_token"]
        self.auth_headers_a = {"HTTP_AUTHORIZATION": f"Bearer {self.token_a}"}

        tokens_b = generate_tokens_for_user(self.user_b)
        self.token_b = tokens_b["access_token"]
        self.auth_headers_b = {"HTTP_AUTHORIZATION": f"Bearer {self.token_b}"}

        # Project for User A with scenes and media
        self.project_a = BookProject.objects.create(
            user=self.user_a,
            title="مشروع المستخدم الأول",
            genre="دراما تاريخية",
            project_type="AUDIO_DRAMA",
            raw_text="سيناريو تجريبي كامل للرواية.",
            total_duration_seconds=120.5
        )
        self.scene_a1 = Scene.objects.create(
            project=self.project_a,
            order=1,
            speaker_name="الراوي",
            raw_text="المشهد الأول من الرواية",
            audio_url="http://169.58.32.179:9100/hexmedia-assets/scene1.mp3",
            duration_seconds=60.0
        )
        self.scene_a2 = Scene.objects.create(
            project=self.project_a,
            order=2,
            speaker_name="طارق",
            raw_text="المشهد الثاني من الرواية",
            image_url="http://169.58.32.179:9100/hexmedia-assets/scene2.jpg",
            audio_url="http://169.58.32.179:9100/hexmedia-assets/scene2.mp3",
            duration_seconds=60.5
        )

        # Project for User B
        self.project_b = BookProject.objects.create(
            user=self.user_b,
            title="مشروع المستخدم الثاني",
            genre="خيال علمي",
            project_type="VIDEO_STUDIO",
            raw_text="نص مشروع المستخدم الثاني."
        )

    def test_profile_media_returns_stats(self):
        """GET /api/profile/media returns audio_tracks, scripts, video_scenes, and aggregated stats."""
        res = self.client.get("/api/profile/media", **self.auth_headers_a)
        self.assertEqual(res.status_code, 200)
        data = res.json()

        self.assertIn("audio_tracks", data)
        self.assertIn("scripts", data)
        self.assertIn("video_scenes", data)
        self.assertIn("stats", data)

        stats = data["stats"]
        self.assertEqual(stats["projects_count"], 1)
        self.assertEqual(stats["audio_tracks_count"], 2)
        self.assertEqual(stats["video_scenes_count"], 1)
        self.assertGreaterEqual(stats["total_duration_seconds"], 120.0)

    def test_rename_project_owner_success(self):
        """PATCH /api/projects/{id}/rename successfully renames owner's project."""
        payload = {"title": "اسم جديد للمشروع"}
        res = self.client.patch(
            f"/api/projects/{self.project_a.id}/rename",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers_a
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data["title"], "اسم جديد للمشروع")

        self.project_a.refresh_from_db()
        self.assertEqual(self.project_a.title, "اسم جديد للمشروع")

    def test_rename_project_unauthorized_user_blocked(self):
        """User B cannot rename User A's project (returns 404 or 403)."""
        payload = {"title": "محاولة اختراق العنوان"}
        res = self.client.patch(
            f"/api/projects/{self.project_a.id}/rename",
            data=json.dumps(payload),
            content_type="application/json",
            **self.auth_headers_b
        )
        self.assertIn(res.status_code, [403, 404])

        self.project_a.refresh_from_db()
        self.assertEqual(self.project_a.title, "مشروع المستخدم الأول")

    def test_delete_project_owner_success(self):
        """DELETE /api/projects/{id} deletes the project and its scenes."""
        res = self.client.delete(
            f"/api/projects/{self.project_a.id}",
            **self.auth_headers_a
        )
        self.assertEqual(res.status_code, 200)
        self.assertFalse(BookProject.objects.filter(id=self.project_a.id).exists())
        self.assertFalse(Scene.objects.filter(project_id=self.project_a.id).exists())

    def test_delete_project_unauthorized_user_blocked(self):
        """User B cannot delete User A's project."""
        res = self.client.delete(
            f"/api/projects/{self.project_a.id}",
            **self.auth_headers_b
        )
        self.assertIn(res.status_code, [403, 404])
        self.assertTrue(BookProject.objects.filter(id=self.project_a.id).exists())

    def test_unauthenticated_requests_blocked(self):
        """Unauthenticated requests return 401."""
        res_media = self.client.get("/api/profile/media")
        self.assertEqual(res_media.status_code, 401)

        res_rename = self.client.patch(
            f"/api/projects/{self.project_a.id}/rename",
            data=json.dumps({"title": "تعديل بدون تصريح"}),
            content_type="application/json"
        )
        self.assertEqual(res_rename.status_code, 401)

        res_delete = self.client.delete(f"/api/projects/{self.project_a.id}")
        self.assertEqual(res_delete.status_code, 401)

    def test_profile_modal_ui_components(self):
        """Verify chat/index.html includes all Profile & Projects Hub DOM components and handlers."""
        res = self.client.get("/")
        self.assertEqual(res.status_code, 200)
        content = res.content.decode("utf-8")

        # Modals
        self.assertIn('id="profileModal"', content)
        self.assertIn('id="projectRenameModal"', content)

        # Dual Entry Points
        self.assertIn('id="sidebarProfileBtn"', content)
        self.assertIn('id="dropdownProfileBtn"', content)

        # Tabs & Content Panes
        self.assertIn('id="profileTabProjects"', content)
        self.assertIn('id="profileTabAudio"', content)
        self.assertIn('id="profileTabVideo"', content)
        self.assertIn('id="profileTabScripts"', content)
        self.assertIn('id="profileTabStats"', content)

        # Metric Elements
        self.assertIn('id="statProjectsCount"', content)
        self.assertIn('id="statAudioCount"', content)
        self.assertIn('id="statVideoCount"', content)
        self.assertIn('id="statDurationMinutes"', content)

        # JavaScript Core Handlers
        self.assertIn("function openProfileModal(", content)
        self.assertIn("function closeProfileModal(", content)
        self.assertIn("function switchProfileTab(", content)
        self.assertIn("function openProjectInChat(", content)
        self.assertIn("function submitRenameProject(", content)
        self.assertIn("function deleteProjectInProfile(", content)
