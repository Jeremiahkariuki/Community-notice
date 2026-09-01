from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class NoticeQuerySet(models.QuerySet):
    def active(self):
        now = timezone.now()
        return self.filter(
            models.Q(expires_at__isnull=True) | models.Q(expires_at__gt=now)
        ).filter(is_resolved=False)


class NoticeManager(models.Manager):
    def get_queryset(self):
        return NoticeQuerySet(self.model, using=self._db)

    def active(self):
        return self.get_queryset().active()


class Notice(models.Model):
    PRIORITY_CHOICES = [
        ("normal", "Normal"),
        ("important", "Important ⚡"),
        ("emergency", "Emergency Alert 🚨"),
    ]

    title = models.CharField(max_length=120)
    description = models.TextField()
    image = models.ImageField(upload_to="notices/%Y/%m/", blank=True, null=True)
    location = models.CharField(
        max_length=150,
        blank=True,
        help_text="e.g. Elm Street, Riverside Estate, or a neighborhood name",
    )
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="notices")
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notices")
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default="normal",
        help_text="Urgency level of this notice",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField(
        blank=True,
        null=True,
        help_text="Optional date and time when this notice automatically expires and disappears from public listings",
    )
    is_resolved = models.BooleanField(default=False)

    objects = NoticeManager()

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False


class NoticeImage(models.Model):
    """Extra photos attached to a notice, beyond the main cover image."""

    notice = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name="extra_images")
    image = models.ImageField(upload_to="notices/gallery/%Y/%m/")
    uploaded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["uploaded_at"]

    def __str__(self):
        return f"Image for {self.notice.title}"


class Comment(models.Model):
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name="comments")
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name="comments")
    body = models.TextField(max_length=1000)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"Comment by {self.author.username} on {self.notice.title}"


class Notification(models.Model):
    """In-app alert shown to a user, e.g. 'someone commented on your notice'."""

    recipient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notifications")
    actor = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="triggered_notifications", null=True, blank=True
    )
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE, related_name="notifications", null=True, blank=True)
    verb = models.CharField(max_length=255)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"To {self.recipient.username}: {self.verb}"