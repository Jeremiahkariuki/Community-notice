from io import BytesIO

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from PIL import Image

from .models import Category, Notice


def make_test_image():
    buf = BytesIO()
    Image.new("RGB", (120, 80), color=(40, 130, 80)).save(buf, format="JPEG")
    buf.seek(0)
    return SimpleUploadedFile("photo.jpg", buf.read(), content_type="image/jpeg")


class NoticeModelTests(TestCase):
    def test_notice_str_returns_title(self):
        user = User.objects.create_user(username="alex", password="testpass123")
        category = Category.objects.create(name="Lost & Found")
        notice = Notice.objects.create(
            title="Lost keys near Main St",
            description="Silver keys, blue keychain",
            category=category,
            posted_by=user,
        )
        self.assertEqual(str(notice), "Lost keys near Main St")


class NoticeViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="alex", password="testpass123")
        self.category = Category.objects.create(name="Events")
        self.notice = Notice.objects.create(
            title="Farmers market this weekend",
            description="Local produce and crafts.",
            category=self.category,
            posted_by=self.user,
        )

    def test_list_view_shows_notice(self):
        response = self.client.get(reverse("notices:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Farmers market this weekend")

    def test_detail_view(self):
        response = self.client.get(reverse("notices:detail", args=[self.notice.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Local produce and crafts.")

    def test_create_requires_login(self):
        response = self.client.get(reverse("notices:create"))
        self.assertEqual(response.status_code, 302)

    def test_authenticated_user_can_create_notice(self):
        self.client.login(username="alex", password="testpass123")
        response = self.client.post(reverse("notices:create"), {
            "title": "Free bookshelf",
            "description": "Solid wood, good condition, porch pickup.",
            "category": self.category.id,
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Notice.objects.filter(title="Free bookshelf").exists())

    def test_authenticated_user_can_create_notice_with_image(self):
        self.client.login(username="alex", password="testpass123")
        response = self.client.post(reverse("notices:create"), {
            "title": "Lost dog near the park",
            "description": "Brown labrador, answers to Max.",
            "category": self.category.id,
            "image": make_test_image(),
        })
        self.assertEqual(response.status_code, 302)
        notice = Notice.objects.get(title="Lost dog near the park")
        self.assertTrue(notice.image)

    def test_home_page_loads(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Stay Informed")

    def test_home_page_shows_latest_notice(self):
        response = self.client.get(reverse("home"))
        self.assertContains(response, "Farmers market this weekend")


class RegistrationTests(TestCase):
    def test_register_page_loads(self):
        response = self.client.get(reverse("register"))
        self.assertEqual(response.status_code, 200)

    def test_user_can_register_and_is_logged_in(self):
        response = self.client.post(reverse("register"), {
            "username": "newuser",
            "first_name": "New",
            "email": "new@example.com",
            "password1": "SuperSecret123!",
            "password2": "SuperSecret123!",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(User.objects.filter(username="newuser").exists())
        # follow-up request should now be authenticated
        response = self.client.get(reverse("notices:create"))
        self.assertEqual(response.status_code, 200)

    def test_register_rejects_mismatched_passwords(self):
        response = self.client.post(reverse("register"), {
            "username": "baduser",
            "first_name": "Bad",
            "email": "bad@example.com",
            "password1": "SuperSecret123!",
            "password2": "DoesNotMatch!",
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username="baduser").exists())
