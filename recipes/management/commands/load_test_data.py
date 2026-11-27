import random
import shutil
from collections import defaultdict
from datetime import timedelta
from decimal import Decimal
from pathlib import Path

from dateutil.relativedelta import relativedelta
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from recipes.models import (
    Allergen,
    DailyMenu,
    Ingredient,
    MealType,
    MenuType,
    Recipe,
    RecipeIngredient,
    Subscription,
    SubscriptionPlan,
    User,
)

TEST_IMAGES = Path(__file__).resolve().parent.parent.parent / "testdata" / "images"


class Command(BaseCommand):
    help = "Заполняет базу тестовыми данными"

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Очистить базу (кроме пользователей)",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            self.stdout.write("Удаляю данные...")
            DailyMenu.objects.all().delete()
            Subscription.objects.all().delete()
            RecipeIngredient.objects.all().delete()
            Recipe.objects.all().delete()
            Ingredient.objects.all().delete()
            Allergen.objects.all().delete()
            MenuType.objects.all().delete()
            MealType.objects.all().delete()
            SubscriptionPlan.objects.all().delete()

            self.stdout.write(self.style.SUCCESS("✅ Данные удалены"))
            return

        self.stdout.write("Загружаю данные...")
        meal_types = self._create_meal_types()
        menu_types = self._create_menu_types()
        allergens = self._create_allergens()
        ingredients = self._create_ingredients(allergens)
        recipes = self._create_recipes(meal_types, menu_types, ingredients)
        subscription_plans = self._create_subscription_plans()
        users = self._create_users()
        subscriptions = self._create_subscriptions(
            users, subscription_plans, meal_types, menu_types, allergens
        )
        self._create_daily_menus(subscriptions, recipes)

        self.stdout.write(self.style.SUCCESS("✅ Тестовые данные загружены"))

    def _create_meal_types(self):
        data = [
            ("Завтрак", 200, 1),
            ("Обед", 300, 2),
            ("Ужин", 400, 3),
            ("Десерт", 100, 4),
        ]
        result = {}
        for name, price, order in data:
            obj, _ = MealType.objects.get_or_create(
                name=name,
                defaults={"price": Decimal(price), "order": order},
            )
            result[name] = obj
        self.stdout.write(f"  Приёмы пищи: {len(result)}")
        return result

    def _create_menu_types(self):
        names = ["Классическое", "Низкоуглеводное", "Вегетарианское", "Кето"]
        result = {}
        for name in names:
            obj, _ = MenuType.objects.get_or_create(name=name)
            result[name] = obj
        self.stdout.write(f"  Типы меню: {len(result)}")
        return result

    def _create_allergens(self):
        names = [
            "Рыба и морепродукты",
            "Мясо",
            "Зерновые",
            "Продукты пчеловодства",
            "Орехи и бобовые",
            "Молочные продукты",
        ]
        result = {}
        for name in names:
            obj, _ = Allergen.objects.get_or_create(name=name)
            result[name] = obj
        self.stdout.write(f"  Аллергены: {len(result)}")
        return result

    def _create_ingredients(self, allergens):
        data = [
            ("Рис", 130, []),
            ("Овощи", 40, []),
            ("Кинза", 23, []),
            ("Куриная грудка", 165, []),
            ("Сливки", 200, ["Молочные продукты"]),
            ("Чеснок", 150, []),
            ("Масло сливочное", 750, ["Молочные продукты"]),
            ("Масло оливковое", 900, []),
            ("Спагетти", 350, ["Зерновые"]),
            ("Бекон", 540, ["Мясо"]),
            ("Яйцо", 155, []),
            ("Пармезан", 350, ["Молочные продукты"]),
            ("Огурец", 15, []),
            ("Помидор", 20, []),
            ("Фета", 260, ["Молочные продукты"]),
            ("Оливки", 145, []),
            ("Булочка", 280, ["Зерновые"]),
            ("Котлета", 250, ["Мясо"]),
            ("Сыр", 350, ["Молочные продукты"]),
            ("Соус", 100, []),
            ("Творог", 120, ["Молочные продукты"]),
            ("Мука", 340, ["Зерновые"]),
            ("Мёд", 300, ["Продукты пчеловодства"]),
            ("Креветки", 100, ["Рыба и морепродукты"]),
            ("Кокосовое молоко", 230, []),
            ("Грибы", 30, []),
            ("Паста том ям", 200, ["Рыба и морепродукты"]),
            ("Говядина", 250, ["Мясо"]),
            ("Перец", 30, []),
            ("Кабачок", 20, []),
            ("Сахар", 400, []),
            ("Картофель", 80, []),
            ("Сметана", 200, ["Молочные продукты"]),
        ]
        result = {}
        for name, calories, allergy_names in data:
            obj, _ = Ingredient.objects.get_or_create(
                name=name,
                defaults={"calories": Decimal(calories)},
            )
            for a in allergy_names:
                obj.allergens.add(allergens[a])
            result[name] = obj
        self.stdout.write(f"  Ингредиенты: {len(result)}")
        return result

    def _create_recipes(self, meal_types, menu_types, ingredients):
        data = [
            (
                "Шафрановый рис с овощами",
                "Ароматный рассыпчатый рис с овощами и специями. Быстрый гарнир на каждый день.",
                "Отварить рис, обжарить овощи, добавить шафран и кинзу.",
                "Обед",
                "Вегетарианское",
                [("Рис", 200), ("Овощи", 200), ("Кинза", 30)],
                "Шафрановый рис с овощами.jpg",
            ),
            (
                "Курица в сливочном соусе",
                "Нежная курица в сливочном соусе с чесноком и травами.",
                "Обжарить курицу, добавить сливки и чеснок, тушить 15 минут.",
                "Обед",
                "Классическое",
                [("Куриная грудка", 300), ("Сливки", 200), ("Чеснок", 10), ("Масло сливочное", 20)],
                "Курица в сливочном соусе.jpg",
            ),
            (
                "Паста Карбонара",
                "Классическая итальянская паста с беконом и сыром.",
                "Отварить спагетти, обжарить бекон, смешать с яйцом и пармезаном.",
                "Ужин",
                "Классическое",
                [("Спагетти", 200), ("Бекон", 150), ("Яйцо", 100), ("Пармезан", 50)],
                "Паста Карбонара.jpg",
            ),
            (
                "Греческий салат",
                "Лёгкий свежий салат с сыром фета и овощами.",
                "Нарезать овощи, добавить фету и оливки, заправить маслом.",
                "Обед",
                "Вегетарианское",
                [("Огурец", 150), ("Помидор", 150), ("Фета", 100), ("Оливки", 50)],
                "Греческий салат.jpg",
            ),
            (
                "Бургер домашний",
                "Сочный бургер с котлетой, сыром и соусом.",
                "Обжарить котлету, собрать бургер с булочкой, сыром и соусом.",
                "Ужин",
                "Классическое",
                [("Булочка", 80), ("Котлета", 150), ("Сыр", 30), ("Соус", 20)],
                "Бургер домашний.jpg",
            ),
            (
                "Творожные панкейки",
                "Пышные панкейки с творогом и мёдом.",
                "Смешать творог, муку, яйцо и мёд, обжарить на сковороде.",
                "Завтрак",
                "Классическое",
                [("Творог", 150), ("Мука", 100), ("Яйцо", 50), ("Мёд", 20)],
                "Творожные панкейки.jpg",
            ),
            (
                "Том ям",
                "Острый тайский суп с креветками и кокосовым молоком.",
                "Довести кокосовое молоко до кипения, добавить креветки, грибы и пасту.",
                "Ужин",
                "Кето",
                [
                    ("Креветки", 200),
                    ("Кокосовое молоко", 200),
                    ("Грибы", 100),
                    ("Паста том ям", 20),
                ],
                "Том ям.jpg",
            ),
            (
                "Стейк с овощами",
                "Сочный говяжий стейк с обжаренными овощами.",
                "Обжарить стейк до нужной прожарки, овощи — на гриле.",
                "Ужин",
                "Низкоуглеводное",
                [("Говядина", 250), ("Перец", 100), ("Кабачок", 150), ("Масло оливковое", 20)],
                "Стейк с овощами.jpg",
            ),
            (
                "Сырники",
                "Классические сырники со сметаной или вареньем.",
                "Смешать творог, яйцо, муку и сахар, обжарить до золотистой корочки.",
                "Завтрак",
                "Классическое",
                [("Творог", 200), ("Яйцо", 50), ("Мука", 50), ("Сахар", 20)],
                "Сырники.jpg",
            ),
            (
                "Драники",
                "Очень вкусные драники как в Минске.",
                "Натереть картошку, добавить яйцо и муку, обжарить.",
                "Завтрак",
                "Классическое",
                [("Картофель", 200), ("Сметана", 100), ("Яйцо", 50), ("Мука", 30)],
                "Рецепт Драников.jpg",
            ),
        ]

        result = []
        image_copied = 0

        for title, description, instruction, meal_type, menu_type, items, image_name in data:
            recipe, created = Recipe.objects.get_or_create(
                title=title,
                defaults={
                    "description": description,
                    "instruction": instruction,
                    "meal_type": meal_types[meal_type],
                    "menu_type": menu_types[menu_type],
                    "image": f"recipes/{image_name}",
                },
            )
            if created:
                for ing_name, quantity in items:
                    RecipeIngredient.objects.create(
                        recipe=recipe,
                        ingredient=ingredients[ing_name],
                        quantity=Decimal(quantity),
                    )
                if self._copy_image(image_name):
                    image_copied += 1
            result.append(recipe)
        self.stdout.write(f"  Рецепты: {len(result)}")
        self.stdout.write(f"  Картинки скопировано: {image_copied}")
        return result

    def _copy_image(self, image_name):
        src = TEST_IMAGES / image_name
        if not src.exists():
            self.stdout.write(self.style.WARNING(f"  ⚠ Нет картинки: {image_name}"))
            return False

        dst_dir = Path(settings.MEDIA_ROOT) / "recipes"
        dst_dir.mkdir(parents=True, exist_ok=True)
        dst = dst_dir / image_name

        if not dst.exists():
            shutil.copy2(src, dst)
        return True

    def _create_subscription_plans(self):
        data = [
            ("1 месяц", 1, 1.00),
            ("3 месяца", 3, 1.60),
            ("6 месяцев", 6, 1.80),
            ("12 месяцев", 12, 2.00),
        ]
        result = {}
        for name, duration_months, multiplier in data:
            obj, _ = SubscriptionPlan.objects.get_or_create(
                name=name,
                defaults={"duration_months": duration_months, "multiplier": Decimal(multiplier)},
            )
            result[name] = obj
        self.stdout.write(f"  Тарифы подписок: {len(result)}")
        return result

    def _create_users(self):
        data = [
            ("ivanov@mail.ru", "username1", "Иван", "Иванов"),
            ("petrov@gmail.com", "username2", "Петр", "Петров"),
        ]
        result = []
        for email, username, first_name, last_name in data:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={"username": username, "first_name": first_name, "last_name": last_name},
            )
            if created:
                user.set_password("123")
                user.save()
            result.append(user)
        self.stdout.write(f"  Пользователи: {len(result)} (пароль: 123)")
        return result

    def _create_subscriptions(self, users, subscription_plans, meal_types, menu_types, allergens):
        data = [
            (0, "1 месяц", 2, ["Завтрак", "Обед", "Ужин"], "Классическое", []),
            (1, "3 месяца", 1, ["Завтрак", "Обед"], "Кето", ["Орехи и бобовые"]),
        ]
        result = []
        for user_id, plan_name, persons_count, meals, menu_name, allergy in data:
            user = users[user_id]
            plan = subscription_plans[plan_name]
            selected_meals = [meal_types[m] for m in meals]
            selected_menu = menu_types[menu_name]
            selected_allergens = [allergens[a] for a in allergy]
            price = Subscription.calculate_price(selected_meals, plan)
            expires_at = timezone.now() + relativedelta(months=plan.duration_months)
            subscription, created = Subscription.objects.get_or_create(
                user=user,
                plan=plan,
                defaults={
                    "expires_at": expires_at,
                    "persons_count": persons_count,
                    "menu_type": selected_menu,
                    "price": price,
                    "is_paid": True,
                },
            )
            if created:
                subscription.meal_types.set(selected_meals)
                subscription.allergy_to.set(selected_allergens)
            result.append(
                {
                    "subscription": subscription,
                    "meal_types": selected_meals,
                    "menu_type": selected_menu,
                    "allergens": selected_allergens,
                    "persons_count": persons_count,
                }
            )
        self.stdout.write(f"  Подписки: {len(result)}")
        return result

    # ---------- Меню на день ----------

    def _create_daily_menus(self, subscriptions_data, recipes):
        today = timezone.now().date()
        count = 0
        recipe_allergen_map = defaultdict(set)
        pairs = RecipeIngredient.objects.values_list("recipe_id", "ingredient__allergens__id")
        for recipe_id, allergen_id in pairs:
            if allergen_id is not None:
                recipe_allergen_map[recipe_id].add(allergen_id)

        for sub_data in subscriptions_data:
            sub = sub_data["subscription"]
            meal_types = sub_data["meal_types"]
            menu_type = sub_data["menu_type"]
            excluded = {a.id for a in sub_data["allergens"]}

            for offset in range(7):
                date = today + timedelta(days=offset)
                daily_menu, created = DailyMenu.objects.get_or_create(
                    subscription=sub,
                    date=date,
                )
                if not created:
                    continue

                chosen = []
                for meal in meal_types:
                    suitable_recipes = [
                        r
                        for r in recipes
                        if r.meal_type_id == meal.id
                        and r.menu_type_id == menu_type.id
                        and not (recipe_allergen_map[r.id] & excluded)
                    ]
                    if suitable_recipes:
                        chosen.append(random.choice(suitable_recipes))

                daily_menu.recipes.set(chosen)
                count += 1

        self.stdout.write(f"  Меню на день: {count}")
