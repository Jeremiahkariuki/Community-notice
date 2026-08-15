from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.shortcuts import render, redirect, get_object_or_404
from django.core.paginator import Paginator
from .models import Notice, Category
from .forms import NoticeForm, SignUpForm


def home(request):
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
    if category_id:
        notices = notices.filter(category_id=category_id)

    paginator = Paginator(notices, 6)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(request, "notices/notice_list.html", {
        "page_obj": page_obj,
        "categories": Category.objects.all(),
        "selected_category": int(category_id) if category_id else None,
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