from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import LoginForm, RegistrationForm


def index(request):
    return render(request, "index.html")


def login_view(request):
    if request.user.is_authenticated:
        return redirect("lk")

    next_url = _safe_next_url(request)

    if request.method == "POST":
        form = LoginForm(request.POST, request=request)
        if form.is_valid():
            login(request, form.user)
            return redirect(next_url or "lk")
    else:
        form = LoginForm()

    return render(request, "auth.html", {"form": form, "next": next_url})


@login_required
def lk_view(request):
    return render(request, "lk.html")


def personal_account(request):
    return render(request, "lk.html")


def order(request):
    return render(request, "order.html")


def _safe_next_url(request):
    """Адрес из ?next=... — только если он ведёт на наш же сайт."""
    next_url = request.POST.get("next") or request.GET.get("next") or ""
    if next_url and url_has_allowed_host_and_scheme(
        next_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return next_url
    return ""


def registration(request):
    if request.user.is_authenticated:
        return redirect("lk")

    if request.method == "POST":
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user, backend="recipes.backends.EmailOrUsernameBackend")
            return redirect("lk")
    else:
        form = RegistrationForm()

    return render(request, "registration.html", {"form": form})


def recipe_detail(request):
    return render(request, "card3.html")
