from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Q
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from .models import Notice, Category
from .forms import NoticeForm, SignUpForm



def home(request):
    """Landing page: hero, live preview of latest notices, features & stats."""
    latest_notices = Notice.objects.select_related("category", "posted_by")[:3]
    context = {
        "latest_notices": latest_notices,
        "member_count": User.objects.count(),
        "notice_count": Notice.objects.count(),
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
    notices = Notice.objects.select_related("category", "posted_by")
    category_id = request.GET.get("category")
    query = request.GET.get("q", "").strip()

    if category_id:
        notices = notices.filter(category_id=category_id)

    if query:
        notices = notices.filter(
            Q(title__icontains=query) | Q(description__icontains=query)
        )

    paginator = Paginator(notices, 6)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "notices/notice_list.html", {
        "page_obj": page_obj,
        "categories": Category.objects.all(),
        "selected_category": int(category_id) if category_id else None,
        "query": query,
    })


def notice_detail(request, pk):
    notice = get_object_or_404(Notice, pk=pk)
    return render(request, "notices/notice_detail.html", {"notice": notice})


@login_required
def notice_create(request):
    if request.method == "POST":
        form = NoticeForm(request.POST, request.FILES)
        if form.is_valid():
            notice = form.save(commit=False)
            notice.posted_by = request.user
            notice.save()
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
            messages.success(request, "Notice updated.")
            return redirect("notices:detail", pk=notice.pk)
    else:
        form = NoticeForm(instance=notice)
    return render(request, "notices/notice_form.html", {"form": form, "editing": True, "notice": notice})


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