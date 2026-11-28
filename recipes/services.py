import calendar
import random

from django.db import transaction
from django.utils import timezone

from .models import DailyMenu, Recipe, Subscription


def add_months(value, months):
    """Прибавляет месяцы к дате; 31 января + 1 месяц = 28 (29) февраля."""
    month_index = value.month - 1 + months
    year = value.year + month_index // 12
    month = month_index % 12 + 1
    day = min(value.day, calendar.monthrange(year, month)[1])
    return value.replace(year=year, month=month, day=day)


@transaction.atomic
def create_subscription(user, *, plan, menu_type, meal_types, persons_count, allergens):
    subscription = Subscription.objects.create(
        user=user,
        plan=plan,
        menu_type=menu_type,
        persons_count=persons_count,
        expires_at=add_months(timezone.now(), plan.duration_months),
        price=Subscription.calculate_price(meal_types, plan),
        # TODO: заглушка оплаты — пока считаем, что оплата всегда проходит.
        # Когда подключим платёжку, здесь должно быть False до подтверждения.
        is_paid=True,
    )
    subscription.meal_types.set(meal_types)
    subscription.allergy_to.set(allergens)
    return subscription


def get_or_create_daily_menu(subscription, date):
    menu, created = DailyMenu.objects.get_or_create(
        subscription=subscription,
        date=date,
    )

    if created:
        _choose_recipes(menu, subscription)

    return DailyMenu.objects.for_subscription(subscription, date).with_recipes()


def _choose_recipes(daily_menu, subscription):
    meal_types = list(subscription.meal_types.order_by('order'))
    excluded = list(subscription.allergy_to.values_list("id", flat=True))

    chosen = []
    for meal in meal_types:
        suitable_recipes = list(
            Recipe.objects.filter(meal_type=meal, menu_type=subscription.menu_type)
            .exclude(recipe_ingredients__ingredient__allergens__id__in=excluded)
            .distinct()
        )
        if suitable_recipes:
            chosen.append(random.choice(suitable_recipes))

    daily_menu.recipes.set(chosen)
