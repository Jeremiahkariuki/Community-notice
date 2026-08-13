from django.contrib import admin
from .models import Category, Notice


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "posted_by", "created_at", "is_resolved", "has_image")
    list_filter = ("category", "is_resolved")
    search_fields = ("title", "description")

    @admin.display(boolean=True, description="Image")
    def has_image(self, obj):
        return bool(obj.image)
