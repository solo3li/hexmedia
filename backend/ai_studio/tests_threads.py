import json
import uuid
from django.test import TestCase, Client
from django.contrib.auth.models import User
from .models import BookProject, ChatThread, ChatMessage
from .auth import generate_tokens_for_user


class ChatThreadAPITests(TestCase):
    def setUp(self):
        self.client = Client()
        self.user_a = User.objects.create_user(
            username="user_a",
            email="user_a@hexmedia.local",
            password="Password123!"
        )
        self.user_b = User.objects.create_user(
            username="user_b",
            email="user_b@hexmedia.local",
            password="Password123!"
        )

        tokens_a = generate_tokens_for_user(self.user_a)
        self.token_a = tokens_a["access_token"]
        self.auth_headers_a = {"HTTP_AUTHORIZATION": f"Bearer {self.token_a}"}

        tokens_b = generate_tokens_for_user(self.user_b)
        self.token_b = tokens_b["access_token"]
        self.auth_headers_b = {"HTTP_AUTHORIZATION": f"Bearer {self.token_b}"}

    def test_create_thread(self):
        res = self.client.post("/api/threads", content_type="application/json", **self.auth_headers_a)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("id", data)
        self.assertEqual(data["title"], "محادثة جديدة")

        thread = ChatThread.objects.get(id=data["id"])
        self.assertEqual(thread.user, self.user_a)
        self.assertFalse(thread.is_deleted)

    def test_list_threads_isolation(self):
        # Create thread for User A
        thread_a = ChatThread.objects.create(user=self.user_a, title="User A Thread")
        # Create thread for User B
        thread_b = ChatThread.objects.create(user=self.user_b, title="User B Thread")

        # User A lists threads
        res = self.client.get("/api/threads", **self.auth_headers_a)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        titles = [t["title"] for t in data]
        self.assertIn("User A Thread", titles)
        self.assertNotIn("User B Thread", titles)

        # User B lists threads
        res = self.client.get("/api/threads", **self.auth_headers_b)
        self.assertEqual(res.status_code, 200)
        data = res.json()
        titles = [t["title"] for t in data]
        self.assertIn("User B Thread", titles)
        self.assertNotIn("User A Thread", titles)

    def test_soft_delete_thread(self):
        thread = ChatThread.objects.create(user=self.user_a, title="To Delete")
        res = self.client.delete(f"/api/threads/{thread.id}", **self.auth_headers_a)
        self.assertEqual(res.status_code, 200)

        thread.refresh_from_db()
        self.assertTrue(thread.is_deleted)

        # Thread must not appear in list
        res = self.client.get("/api/threads", **self.auth_headers_a)
        titles = [t["title"] for t in res.json()]
        self.assertNotIn("To Delete", titles)

    def test_cross_user_thread_access_forbidden(self):
        thread_b = ChatThread.objects.create(user=self.user_b, title="Private Thread B")

        # User A tries to delete User B's thread -> 404
        res = self.client.delete(f"/api/threads/{thread_b.id}", **self.auth_headers_a)
        self.assertEqual(res.status_code, 404)

        # User A tries to rename User B's thread -> 404
        res = self.client.patch(
            f"/api/threads/{thread_b.id}/rename",
            data=json.dumps({"title": "Hacked"}),
            content_type="application/json",
            **self.auth_headers_a
        )
        self.assertEqual(res.status_code, 404)

    def test_rename_thread(self):
        thread = ChatThread.objects.create(user=self.user_a, title="Original Title")
        res = self.client.patch(
            f"/api/threads/{thread.id}/rename",
            data=json.dumps({"title": "Updated Title"}),
            content_type="application/json",
            **self.auth_headers_a
        )
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json()["title"], "Updated Title")

        thread.refresh_from_db()
        self.assertEqual(thread.title, "Updated Title")

    def test_get_thread_messages(self):
        thread = ChatThread.objects.create(user=self.user_a, title="Chat with messages")
        ChatMessage.objects.create(
            user=self.user_a,
            thread=thread,
            role="USER",
            content="Hello AI",
            msg_type="TEXT"
        )
        ChatMessage.objects.create(
            user=self.user_a,
            thread=thread,
            role="ASSISTANT",
            content="Hello User!",
            msg_type="TEXT"
        )

        res = self.client.get(f"/api/threads/{thread.id}/messages", **self.auth_headers_a)
        self.assertEqual(res.status_code, 200)
        msgs = res.json()
        self.assertEqual(len(msgs), 2)
        self.assertEqual(msgs[0]["content"], "Hello AI")
        self.assertEqual(msgs[1]["content"], "Hello User!")

    def test_generate_title_endpoint(self):
        thread = ChatThread.objects.create(user=self.user_a, title="محادثة جديدة")
        ChatMessage.objects.create(
            user=self.user_a,
            thread=thread,
            role="USER",
            content="رواية مغامرات في أعماق البحار والمحيطات المظلمة",
            msg_type="TEXT"
        )

        res = self.client.post(
            f"/api/threads/{thread.id}/generate-title",
            content_type="application/json",
            **self.auth_headers_a
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data["success"])
        thread.refresh_from_db()
        self.assertIn("البحار", thread.title)
