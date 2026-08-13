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
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="notices")
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="notices")
    created_at = models.DateTimeField(auto_now_add=True)
    is_resolved = models.BooleanField(default=False)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title
