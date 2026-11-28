from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import redirect_to_login
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme

from .forms import MAX_PERSONS, LoginForm, OrderForm, ProfileForm, RegistrationForm
from .services import create_subscription

MENU_IMAGES = {
    "classic": "img/menu_classical.png",
    "low": "img/menu_nizkougl.png",
    "veg": "img/menu_veg.png",
    "keto": "img/menu_keto.png",
}
DEFAULT_MENU_IMAGE = "img/menu_classical.png"


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


def _order_context(request, form):
    menu_types = [
        {"obj": menu, "image": MENU_IMAGES.get(menu.slug, DEFAULT_MENU_IMAGE), "number": number}
        for number, menu in enumerate(form.fields["menu_type"].queryset, start=1)
    ]
    plans = list(form.fields["plan"].queryset)
    allergens = list(form.fields["allergies"].queryset)

    if form.is_bound:
        # Показываем то, что человек уже выбрал (например, после ошибки)
        selected_menu = form.data.get("menu_type", "")
        selected_plan = form.data.get("plan", "")
        selected_persons = form.data.get("persons_count", "1")
        selected_allergies = form.data.getlist("allergies")
        meal_rows = [
            {"meal": meal, "checked": form.data.get(f"meal_{meal.pk}") == "1"}
            for meal in form.meals
        ]
    else:
        # ?menu=veg на ссылке заранее выбирает тарелку
        selected_menu = request.GET.get("menu", "")
        selected_plan = str(plans[0].pk) if plans else ""
        selected_persons = "1"
        selected_allergies = []
        meal_rows = [{"meal": meal, "checked": True} for meal in form.meals]

    # Данные для подсчёта стоимости на странице (итоговая цена считается на сервере)
    pricing = {
        "plans": {
            str(plan.pk): {"months": plan.duration_months, "multiplier": str(plan.multiplier)}
            for plan in plans
        },
        "meals": {str(meal.pk): str(meal.price) for meal in form.meals},
    }

    return {
        "form": form,
        "menu_types": menu_types,
        "plans": plans,
        "meal_rows": meal_rows,
        "persons_range": range(1, MAX_PERSONS + 1),
        "allergens": allergens,
        "selected_menu": selected_menu,
        "selected_plan": selected_plan,
        "selected_persons": selected_persons,
        "selected_allergies": selected_allergies,
        "pricing": pricing,
    }


def order(request):
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect_to_login(request.path)

        form = OrderForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            create_subscription(
                request.user,
                plan=data["plan"],
                menu_type=data["menu_type"],
                meal_types=form.selected_meals,
                persons_count=data["persons_count"],
                allergens=data["allergies"],
            )
            messages.success(request, "Подписка оформлена! Спасибо за заказ.")
            return redirect("lk")
    else:
        form = OrderForm()

    return render(request, "order.html", _order_context(request, form))


def personal_account(request):
    return render(request, "lk.html")


def index(request):
    return render(request, "index.html")


def recipe_detail(request):
    return render(request, "card3.html")
