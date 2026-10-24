from django.test import TestCase
from django.apps import apps
from django.contrib.auth.models import User
from core.models import AIConfiguration, ChatThread, ChatMessage
from book_drama.models import BookProject, Character, Chapter
from image_video.models import Scene, TimelineState
from core.services import build_history_window
from story_writer.services import build_director_instruction


class ModularArchitectureTests(TestCase):
    def test_all_modular_apps_registered(self):
        """Verify that all 4 modular apps plus ai_studio are registered in Django."""
        installed = [app.name for app in apps.get_app_configs()]
        self.assertIn('core', installed)
        self.assertIn('book_drama', installed)
        self.assertIn('story_writer', installed)
        self.assertIn('image_video', installed)
        self.assertIn('ai_studio', installed)

    def test_database_table_names_preserved(self):
        """Ensure db_table preserves backward compatibility with existing PostgreSQL tables."""
        self.assertEqual(AIConfiguration._meta.db_table, 'ai_studio_aiconfiguration')
        self.assertEqual(ChatThread._meta.db_table, 'ai_studio_chatthread')
        self.assertEqual(ChatMessage._meta.db_table, 'ai_studio_chatmessage')
        self.assertEqual(BookProject._meta.db_table, 'ai_studio_bookproject')
        self.assertEqual(Character._meta.db_table, 'ai_studio_character')
        self.assertEqual(Chapter._meta.db_table, 'ai_studio_chapter')
        self.assertEqual(Scene._meta.db_table, 'ai_studio_scene')
        self.assertEqual(TimelineState._meta.db_table, 'ai_studio_timelinestate')

    def test_cross_app_relationships(self):
        """Verify models across core, book_drama, and image_video relate seamlessly."""
        user = User.objects.create_user(username="mod_user", email="mod@test.local", password="pass")
        project = BookProject.objects.create(
            user=user,
            title="مشروع تجريبي للربط",
            genre="أدب"
        )
        thread = ChatThread.objects.create(
            user=user,
            project=project,
            title="محادثة المشروع"
        )
        scene = Scene.objects.create(
            project=project,
            order=1,
            speaker_name="الراوي",
            raw_text="بداية الحكاية"
        )

        self.assertEqual(thread.project.id, project.id)
        self.assertEqual(project.scenes.count(), 1)
        self.assertEqual(project.scenes.first().id, scene.id)
        self.assertEqual(project.threads.first().id, thread.id)

    def test_modular_services(self):
        """Verify modular services execute cleanly."""
        instruction = build_director_instruction("قصة الصحراء", "راوي، بطل", narration_mode="SMART")
        self.assertIn("قصة الصحراء", instruction)
        self.assertIn("المخرج الصوتي", instruction)
