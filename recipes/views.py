from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils import timezone

from .forms import LoginForm, RegistrationForm, ProfileForm


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
    user = request.user
    if request.method == "POST":
        profile_form = ProfileForm(request.POST, instance=user)
        if profile_form.is_valid():
            profile_form.save()
            return redirect("lk")
    else:
        profile_form = ProfileForm(instance=user)
    subscriptions = user.subscriptions.filter(
        is_paid=True, expires_at__gt=timezone.now())
    for subscription in subscriptions:
        daily_menu = subscription.daily_menus.filter(
            date=timezone.localdate()).first()
        total_calories = 0
        if daily_menu:
            recipes = daily_menu.recipes.all()
            for recipe in recipes:
                total_calories += recipe.total_calories
        subscription.daily_calories = total_calories
    context = {
        'user': user,
        'subscriptions': subscriptions,
        'profile_form': profile_form,
    }

    return render(request, "lk.html", context)


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
