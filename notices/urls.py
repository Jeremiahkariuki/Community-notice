from django.urls import path
from . import views

app_name = "notices"

urlpatterns = [
    path("", views.notice_list, name="list"),
    path("mine/", views.my_notices, name="mine"),
    path("new/", views.notice_create, name="create"),
    path("notifications/", views.notification_list, name="notifications"),
    path("notifications/<int:pk>/read/", views.notification_mark_read, name="notification_read"),
    path("<int:pk>/", views.notice_detail, name="detail"),
    path("<int:pk>/edit/", views.notice_edit, name="edit"),
    path("<int:pk>/delete/", views.notice_delete, name="delete"),
    path("<int:pk>/comments/<int:comment_pk>/delete/", views.comment_delete, name="comment_delete"),
]