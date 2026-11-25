from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from .models import (
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

# Пользователь ==============


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "username", "first_name", "last_name", "is_staff")
    list_filter = ("is_staff", "is_superuser", "is_active")
    search_fields = ("email", "username", "first_name", "last_name")

    fieldsets = (
        (None, {"fields": ("email", "username", "password")}),
        ("Личная информация", {"fields": ("first_name", "last_name")}),
        (
            "Права",
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        ("Даты", {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "username", "password1", "password2"),
            },
        ),
    )


# Справочники ==============


@admin.register(MealType)
class MealTypeAdmin(admin.ModelAdmin):
    list_display = ("name", "price", "order")
    list_editable = ("price", "order")
    ordering = ("order",)


@admin.register(MenuType)
class MenuTypeAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Allergen)
class AllergenAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


@admin.register(Ingredient)
class IngredientAdmin(admin.ModelAdmin):
    list_display = ("name", "calories")
    search_fields = ("name",)


# Рецепт ==============


class RecipeIngredientInline(admin.TabularInline):
    model = RecipeIngredient
    extra = 1
    raw_id_fields = ("ingredient",)


@admin.register(Recipe)
class RecipeAdmin(admin.ModelAdmin):
    list_display = ("title", "meal_type", "menu_type", "image_preview")
    list_select_related = ("meal_type", "menu_type")
    list_filter = ("meal_type", "menu_type")
    search_fields = ("title", "description")
    readonly_fields = ("image_preview",)
    inlines = [RecipeIngredientInline]
    fieldsets = (
        (None, {"fields": ("title", "description", "instruction", "image", "image_preview")}),
        ("Классификация", {"fields": ("meal_type", "menu_type")}),
    )

    @admin.display(description="калорийность 1 порции")
    def calories_display(self, obj):
        return f"{obj.total_calories:.2f} ккал"

    @admin.display(description="изображение")
    def image_preview(self, obj):
        if obj.image:
            return format_html("<img src='{}' style='max-height: 200px;' />", obj.image.url)
        return "—"


# Подписки ==============


@admin.register(SubscriptionPlan)
class SubscriptionPlanAdmin(admin.ModelAdmin):
    list_display = ("name", "duration_months", "multiplier", "is_active")
    list_editable = ("multiplier", "is_active")
    ordering = ("name",)


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "plan", "started_at", "expires_at", "persons_count", "price", "is_paid")
    list_filter = ("is_paid", "plan")
    search_fields = ("user__email", "user__username")
    readonly_fields = ("started_at",)

    fieldsets = (
        (None, {"fields": ("user", "plan", "price", "is_paid")}),
        ("Сроки", {"fields": ("started_at", "expires_at")}),
        (
            "Настройки подборки",
            {"fields": ("persons_count", "meal_types", "menu_types", "allergy_to")},
        ),
    )

    @admin.display(description="активна", boolean=True)
    def is_active_display(self, obj):
        return obj.is_active


# Меню на день ==============


@admin.register(DailyMenu)
class DailyMenuAdmin(admin.ModelAdmin):
    list_display = ("subscription", "date")
    list_filter = ("date",)
    search_fields = ("subscription__user__email",)
