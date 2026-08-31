from django.contrib import admin
from .models import Category, Notice, NoticeImage, Comment, Notification


class NoticeImageInline(admin.TabularInline):
    model = NoticeImage
    extra = 1


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)


@admin.register(Notice)
class NoticeAdmin(admin.ModelAdmin):
    list_display = ("title", "category", "location", "posted_by", "created_at", "is_resolved", "has_image")
    list_filter = ("category", "is_resolved")
    search_fields = ("title", "description", "location")
    inlines = [NoticeImageInline]

    @admin.display(boolean=True, description="Image")
    def has_image(self, obj):
        return bool(obj.image)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ("notice", "author", "created_at")
    search_fields = ("body",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("recipient", "actor", "notice", "verb", "is_read", "created_at")
    list_filter = ("is_read",)