from decimal import Decimal

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import UserManager as BaseUserManager
from django.db import models
from django.utils import timezone


class MealType(models.Model):
    name = models.CharField("название", max_length=100, unique=True)
    price = models.DecimalField(
        "цена за месяц в тарифе", max_digits=10, decimal_places=2, default=0
    )
    order = models.PositiveSmallIntegerField("порядок", default=0)

    class Meta:
        verbose_name = "приём пищи"
        verbose_name_plural = "приёмы пищи"
        ordering = ["order"]

    def __str__(self):
        return self.name


class MenuType(models.Model):
    name = models.CharField("название", max_length=100, unique=True)

    class Meta:
        verbose_name = "тип меню"
        verbose_name_plural = "типы меню"

    def __str__(self):
        return self.name


class Allergen(models.Model):
    name = models.CharField("название", max_length=100, unique=True)

    class Meta:
        verbose_name = "аллерген"
        verbose_name_plural = "аллергены"

    def __str__(self):
        return self.name


class Ingredient(models.Model):
    name = models.CharField("название", max_length=200, unique=True)
    calories = models.DecimalField(
        "калорийность на 100г", max_digits=7, decimal_places=2, default=0
    )
    allergens = models.ManyToManyField(
        Allergen, verbose_name="аллергены", blank=True, related_name="ingredients"
    )

    class Meta:
        verbose_name = "ингредиент"
        verbose_name_plural = "ингредиенты"

    def __str__(self):
        return self.name


class Recipe(models.Model):
    title = models.CharField("название", max_length=200)
    description = models.CharField("мини-описание", max_length=250, blank=True)
    instruction = models.TextField("инструкция приготовления")

    image = models.ImageField("изображение", upload_to="recipes/")

    meal_type = models.ForeignKey(
        MealType, verbose_name="приём пищи", on_delete=models.PROTECT, related_name="recipes"
    )
    menu_type = models.ForeignKey(
        MenuType, verbose_name="тип меню", on_delete=models.PROTECT, related_name="recipes"
    )
    ingredients = models.ManyToManyField(
        Ingredient, verbose_name="ингредиенты", through="RecipeIngredient", related_name="recipes"
    )

    created_at = models.DateTimeField("создан", auto_now_add=True)

    class Meta:
        verbose_name = "рецепт"
        verbose_name_plural = "рецепты"

    def __str__(self):
        return self.title

    @property
    def total_calories(self):
        return sum((ri.get_calories() for ri in self.recipe_ingredients.all()), Decimal("0"))


class RecipeIngredient(models.Model):
    recipe = models.ForeignKey(
        Recipe, verbose_name="рецепт", on_delete=models.CASCADE, related_name="recipe_ingredients"
    )
    ingredient = models.ForeignKey(
        Ingredient,
        verbose_name="ингредиент",
        on_delete=models.PROTECT,
        related_name="ingredient_recipes",
    )
    quantity = models.DecimalField("количество (граммы)", max_digits=10, decimal_places=2)

    class Meta:
        verbose_name = "ингредиент рецепта"
        verbose_name_plural = "ингредиенты рецепта"
        unique_together = ("recipe", "ingredient")

    def __str__(self):
        return f"{self.ingredient} — {self.quantity} г"

    def get_calories(self):
        return self.quantity * self.ingredient.calories / 100


# ============================================


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("Email обязателен")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = models.CharField("логин", max_length=150, unique=True, blank=True, null=True)
    email = models.EmailField("почта", unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    objects = UserManager()

    class Meta:
        verbose_name = "пользователь"
        verbose_name_plural = "пользователи"


# ============================


class SubscriptionPlan(models.Model):
    name = models.CharField("название", max_length=40, unique=True)
    duration_months = models.PositiveSmallIntegerField("длительность (месяцев)")
    multiplier = models.DecimalField(
        "множитель стоимости", max_digits=4, decimal_places=2, default=1.00
    )
    is_active = models.BooleanField("активен", default=True)

    class Meta:
        verbose_name = "тариф подписки"
        verbose_name_plural = "тарифы подписок"
        ordering = ["name"]

    def __str__(self):
        return self.name


class Subscription(models.Model):
    user = models.ForeignKey(
        User, verbose_name="пользователь", on_delete=models.CASCADE, related_name="subscriptions"
    )
    plan = models.ForeignKey(SubscriptionPlan, verbose_name="тариф", on_delete=models.PROTECT)

    started_at = models.DateTimeField("дата начала", auto_now_add=True)
    expires_at = models.DateTimeField("дата окончания")

    persons_count = models.PositiveSmallIntegerField("количество персон", default=1)
    meal_types = models.ManyToManyField(
        MealType, verbose_name="приёмы пищи", related_name="subscriptions"
    )
    menu_type = models.ForeignKey(
        MenuType, verbose_name="тип меню", on_delete=models.PROTECT, related_name="subscriptions"
    )
    allergy_to = models.ManyToManyField(
        Allergen, verbose_name="аллергия на", blank=True, related_name="subscriptions"
    )
    price = models.DecimalField(
        "цена на момент покупки", max_digits=10, decimal_places=2, default=0
    )
    is_paid = models.BooleanField("оплачено", default=True)

    class Meta:
        verbose_name = "подписка"
        verbose_name_plural = "подписки"

    def __str__(self):
        return f"{self.user} — {self.plan}"

    @property
    def is_active(self):
        return self.is_paid and self.expires_at > timezone.now()


class DailyMenu(models.Model):
    subscription = models.ForeignKey(
        Subscription, verbose_name="подписка", on_delete=models.CASCADE, related_name="daily_menus"
    )
    date = models.DateField("дата")
    recipes = models.ManyToManyField(Recipe, verbose_name="рецепты", related_name="daily_menus")

    class Meta:
        verbose_name = "меню на день"
        verbose_name_plural = "меню на день"
        unique_together = ("subscription", "date")

    def __str__(self):
        return f"{self.subscription} — {self.date}"
