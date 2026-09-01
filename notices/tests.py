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


class AdminDashboardTests(TestCase):
    def setUp(self):
        self.regular_user = User.objects.create_user(username="member", password="password123")
        self.admin_user = User.objects.create_superuser(username="adminuser", email="admin@test.com", password="adminpassword123")
        self.category = Category.objects.create(name="General")
        self.notice = Notice.objects.create(
            title="Test Notice",
            description="Test Description",
            category=self.category,
            posted_by=self.regular_user,
        )

    def test_regular_user_cannot_access_admin_dashboard(self):
        self.client.login(username="member", password="password123")
        response = self.client.get(reverse("admin_dashboard"))
        # user_passes_test redirects unauthorized logged in users
        self.assertEqual(response.status_code, 302)

    def test_super_admin_can_access_admin_dashboard(self):
        self.client.login(username="adminuser", password="adminpassword123")
        response = self.client.get(reverse("admin_dashboard"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "System Overview & Controls")
        self.assertContains(response, "Test Notice")

    def test_super_admin_can_add_category(self):
        self.client.login(username="adminuser", password="adminpassword123")
        response = self.client.post(reverse("admin_dashboard"), {
            "action": "add_category",
            "category_name": "Emergency Alerts",
        })
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Category.objects.filter(name="Emergency Alerts").exists())

    def test_super_admin_can_toggle_notice_resolved(self):
        self.client.login(username="adminuser", password="adminpassword123")
        response = self.client.post(reverse("admin_dashboard"), {
            "action": "toggle_resolved",
            "notice_id": self.notice.pk,
        })
        self.assertEqual(response.status_code, 302)
        self.notice.refresh_from_db()
        self.assertTrue(self.notice.is_resolved)


class NoticeSearchTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="searcher", password="testpass123")
        self.category = Category.objects.create(name="Events")
        self.match = Notice.objects.create(
            title="Youth Football Tournament",
            description="Registrations are now open for the summer tournament.",
            category=self.category,
            posted_by=self.user,
        )
        self.no_match = Notice.objects.create(
            title="Water Interruption",
            description="Water supply will be off 8am to 12pm.",
            category=self.category,
            posted_by=self.user,
        )

    def test_search_matches_title(self):
        response = self.client.get(reverse("notices:list"), {"q": "Football"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Youth Football Tournament")
        self.assertNotContains(response, "Water Interruption")

    def test_search_matches_description(self):
        response = self.client.get(reverse("notices:list"), {"q": "registrations"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Youth Football Tournament")

    def test_search_is_case_insensitive(self):
        response = self.client.get(reverse("notices:list"), {"q": "football"})
        self.assertContains(response, "Youth Football Tournament")

    def test_empty_search_shows_all_notices(self):
        response = self.client.get(reverse("notices:list"))
        self.assertContains(response, "Youth Football Tournament")
        self.assertContains(response, "Water Interruption")

    def test_search_with_no_matches_shows_empty_state(self):
        response = self.client.get(reverse("notices:list"), {"q": "nonexistentxyz"})
        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "Youth Football Tournament")
        self.assertNotContains(response, "Water Interruption")


class NoticeExpirationTests(TestCase):
    def setUp(self):
        from datetime import timedelta
        from django.utils import timezone

        self.user = User.objects.create_user(username="timer", password="password123")
        self.category = Category.objects.create(name="Alerts")

        self.active_notice = Notice.objects.create(
            title="Active Emergency Notice",
            description="Still valid notice",
            category=self.category,
            posted_by=self.user,
            expires_at=timezone.now() + timedelta(days=2),
        )

        self.expired_notice = Notice.objects.create(
            title="Old Past Notice",
            description="This notice has expired",
            category=self.category,
            posted_by=self.user,
            expires_at=timezone.now() - timedelta(hours=1),
        )

    def test_is_expired_property(self):
        self.assertFalse(self.active_notice.is_expired)
        self.assertTrue(self.expired_notice.is_expired)

    def test_active_queryset_filters_out_expired(self):
        active_notices = Notice.objects.active()
        self.assertIn(self.active_notice, active_notices)
        self.assertNotIn(self.expired_notice, active_notices)

    def test_notice_list_view_hides_expired_by_default(self):
        response = self.client.get(reverse("notices:list"))
        self.assertContains(response, "Active Emergency Notice")
        self.assertNotContains(response, "Old Past Notice")

    def test_notice_list_view_shows_expired_when_filtered(self):
        response = self.client.get(reverse("notices:list"), {"status": "expired"})
        self.assertContains(response, "Old Past Notice")
        self.assertNotContains(response, "Active Emergency Notice")