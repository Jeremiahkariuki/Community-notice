"""
URL configuration for communotice project.
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

from notices import views as notice_views

urlpatterns = [
    path('admin/', admin.site.urls),

    # Landing page
    path('', notice_views.home, name='home'),

    # Auth
    path('accounts/register/', notice_views.register, name='register'),
    path('accounts/profile/', notice_views.profile, name='profile'),
    path('accounts/admin-dashboard/', notice_views.admin_dashboard, name='admin_dashboard'),
    path('accounts/login/', auth_views.LoginView.as_view(template_name='registration/login.html'), name='login'),
    path('accounts/logout/', auth_views.LogoutView.as_view(next_page='home'), name='logout'),


    # Notices
    path('notices/', include('notices.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)