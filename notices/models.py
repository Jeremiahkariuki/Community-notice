from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Notice(models.Model):
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
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


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