from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import Notice, Category, NoticeImage, Comment, Notification
from .forms import NoticeForm, SignUpForm, CommentForm


def notify(recipient, verb, actor=None, notice=None):
    """Create an in-app notification, skipping self-notifications."""
    if recipient is None or (actor is not None and recipient == actor):
        return
    Notification.objects.create(recipient=recipient, actor=actor, notice=notice, verb=verb)


from django.db import models
from django.utils import timezone


def home(request):
    """Landing page: hero, live preview of latest active notices, features & stats."""
    ensure_default_categories()
    latest_notices = (
        Notice.objects.active()
        .select_related("category", "posted_by")
        .annotate(
            priority_order=models.Case(
                models.When(priority="emergency", then=models.Value(1)),
                models.When(priority="important", then=models.Value(2)),
                default=models.Value(3),
                output_field=models.IntegerField(),
            )
        )
        .order_by("priority_order", "-created_at")[:3]
    )
    context = {
        "latest_notices": latest_notices,
        "member_count": User.objects.count(),
        "notice_count": Notice.objects.active().count(),
        "category_count": Category.objects.count(),
    }
    return render(request, "notices/home.html", context)


def register(request):
    if request.user.is_authenticated:
        return redirect("notices:list")

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, f"Welcome to CommuNotice, {user.first_name or user.username}!")
            return redirect("notices:list")
    else:
        form = SignUpForm()
    return render(request, "registration/register.html", {"form": form})


def notice_list(request):
    status_filter = request.GET.get("status", "active")
    now = timezone.now()

    if status_filter == "all":
        notices = Notice.objects.select_related("category", "posted_by")
    elif status_filter == "expired":
        notices = Notice.objects.filter(expires_at__lte=now).select_related("category", "posted_by")
    else:
        notices = Notice.objects.active().select_related("category", "posted_by")

    category_id = request.GET.get("category")
    if category_id:
        notices = notices.filter(category_id=category_id)

    priority_filter = request.GET.get("priority")
    if priority_filter in ["emergency", "important", "normal"]:
        notices = notices.filter(priority=priority_filter)

    q = request.GET.get("q")
    if q:
        notices = notices.filter(models.Q(title__icontains=q) | models.Q(description__icontains=q))

    paginator = Paginator(notices, 6)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "notices/notice_list.html", {
        "page_obj": page_obj,
        "categories": Category.objects.all(),
        "selected_category": int(category_id) if category_id else None,
        "selected_priority": priority_filter or "",
        "status_filter": status_filter,
        "search_query": q or "",
    })


def notice_detail(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    comments = notice.comments.select_related("author")

    if request.method == "POST":
        if not request.user.is_authenticated:
            messages.error(request, "Please log in to comment.")
            return redirect("login")
        comment_form = CommentForm(request.POST)
        if comment_form.is_valid():
            comment = comment_form.save(commit=False)
            comment.notice = notice
            comment.author = request.user
            comment.save()
            notify(
                recipient=notice.posted_by,
                actor=request.user,
                notice=notice,
                verb=f"{request.user.username} commented on your notice \"{notice.title}\".",
            )
            messages.success(request, "Comment posted.")
            return redirect("notices:detail", pk=notice.pk)
    else:
        comment_form = CommentForm()

    return render(request, "notices/notice_detail.html", {
        "notice": notice,
        "comments": comments,
        "comment_form": comment_form,
        "gallery_images": notice.extra_images.all(),
    })


@login_required
def comment_delete(request, pk, comment_pk):
    notice = get_object_or_404(Notice, pk=pk)
    comment = get_object_or_404(Comment, pk=comment_pk, notice=notice)
    if comment.author != request.user and notice.posted_by != request.user:
        messages.error(request, "You can only delete your own comments.")
        return redirect("notices:detail", pk=notice.pk)
    if request.method == "POST":
        comment.delete()
        messages.success(request, "Comment deleted.")
    return redirect("notices:detail", pk=notice.pk)


DEFAULT_CATEGORIES = [
    "Announcements",
    "Emergency & Safety",
    "Events & Sports",
    "Lost & Found",
    "Services & Maintenance",
    "General Discussion",
]


def ensure_default_categories():
    if not Category.objects.exists():
        for cat_name in DEFAULT_CATEGORIES:
            Category.objects.get_or_create(name=cat_name)


@login_required
def notice_create(request):
    ensure_default_categories()
    if request.method == "POST":
        form = NoticeForm(request.POST, request.FILES)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.posted_by = request.user
            notice.save()
            for extra_image in form.cleaned_data.get("extra_images") or []:
                NoticeImage.objects.create(notice=notice, image=extra_image)
            messages.success(request, "Your notice has been posted.")
            return redirect("notices:detail", pk=notice.pk)
    else:
        form = NoticeForm()
    return render(request, "notices/notice_form.html", {"form": form})


@login_required
def my_notices(request):
    notices = Notice.objects.filter(posted_by=request.user).select_related("category")
    paginator = Paginator(notices, 6)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "notices/my_notices.html", {"page_obj": page_obj})


@login_required
def notice_edit(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    if notice.posted_by != request.user:
        messages.error(request, "You can only edit notices you posted.")
        return redirect("notices:detail", pk=notice.pk)

    if request.method == "POST":
        form = NoticeForm(request.POST, request.FILES, instance=notice)
        if form.is_valid():
            form.save()
            for extra_image in form.cleaned_data.get("extra_images") or []:
                NoticeImage.objects.create(notice=notice, image=extra_image)
            remove_ids = request.POST.getlist("remove_image")
            if remove_ids:
                NoticeImage.objects.filter(notice=notice, pk__in=remove_ids).delete()
            messages.success(request, "Notice updated.")
            return redirect("notices:detail", pk=notice.pk)
    else:
        form = NoticeForm(instance=notice)
    return render(request, "notices/notice_form.html", {
        "form": form,
        "editing": True,
        "notice": notice,
        "gallery_images": notice.extra_images.all(),
    })


@login_required
def notice_delete(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    if notice.posted_by != request.user:
        messages.error(request, "You can only delete notices you posted.")
        return redirect("notices:detail", pk=notice.pk)

    if request.method == "POST":
        notice.delete()
        messages.success(request, "Notice deleted.")
        return redirect("notices:mine")
    return render(request, "notices/notice_confirm_delete.html", {"notice": notice})


@login_required
def notification_list(request):
    notifications = request.user.notifications.select_related("actor", "notice")
    notifications.filter(is_read=False).update(is_read=True)
    paginator = Paginator(notifications, 15)
    page_obj = paginator.get_page(request.GET.get("page"))
    return render(request, "notices/notification_list.html", {"page_obj": page_obj})


@login_required
def notification_mark_read(request, pk):
    notification = get_object_or_404(Notification, pk=pk, recipient=request.user)
    notification.is_read = True
    notification.save(update_fields=["is_read"])
    if notification.notice_id:
        return redirect("notices:detail", pk=notification.notice_id)
    return redirect("notices:notifications")


@login_required
def profile(request):
    context = {
        "notice_count": Notice.objects.filter(posted_by=request.user).count(),
        "recent_notices": Notice.objects.filter(posted_by=request.user).select_related("category")[:5],
    }
    return render(request, "registration/profile.html", context)


@login_required
@user_passes_test(lambda u: u.is_staff or u.is_superuser)
def admin_dashboard(request):
    if request.method == "POST":
        action = request.POST.get("action")
        if action == "add_category":
            name = request.POST.get("category_name", "").strip()
            if name:
                category, created = Category.objects.get_or_create(name=name)
                if created:
                    messages.success(request, f"Category '{name}' created successfully.")
                else:
                    messages.warning(request, f"Category '{name}' already exists.")
            else:
                messages.error(request, "Category name cannot be empty.")

        elif action == "toggle_resolved":
            notice_id = request.POST.get("notice_id")
            notice = get_object_or_404(Notice, pk=notice_id)
            notice.is_resolved = not notice.is_resolved
            notice.save()
            status_str = "resolved" if notice.is_resolved else "active"
            messages.success(request, f"Notice '{notice.title}' marked as {status_str}.")

        elif action == "delete_notice":
            notice_id = request.POST.get("notice_id")
            notice = get_object_or_404(Notice, pk=notice_id)
            title = notice.title
            notice.delete()
            messages.success(request, f"Notice '{title}' deleted by admin.")

        elif action == "toggle_staff":
            user_id = request.POST.get("user_id")
            target_user = get_object_or_404(User, pk=user_id)
            if target_user == request.user:
                messages.error(request, "You cannot alter your own staff permissions.")
            else:
                target_user.is_staff = not target_user.is_staff
                target_user.save()
                status_str = "Staff Admin" if target_user.is_staff else "Regular Member"
                messages.success(request, f"User '{target_user.username}' updated to {status_str}.")

        return redirect("admin_dashboard")

    context = {
        "member_count": User.objects.count(),
        "notice_count": Notice.objects.count(),
        "active_notice_count": Notice.objects.filter(is_resolved=False).count(),
        "resolved_notice_count": Notice.objects.filter(is_resolved=True).count(),
        "category_count": Category.objects.count(),
        "categories": Category.objects.all(),
        "all_users": User.objects.order_by("-date_joined"),
        "recent_notices": Notice.objects.select_related("category", "posted_by").all()[:10],
    }
    return render(request, "registration/admin_dashboard.html", context)