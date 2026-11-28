from django.shortcuts import render

from recipes.models import Recipe




def home(request):
    recipes = Recipe.objects.select_related("meal_type").order_by("?")[:5]
    return render(request, "index.html", {"recipes": recipes})


def auth(request):
    return render(request, "auth.html")


def personal_account(request):
    return render(request, "lk.html")


def order(request):
    return render(request, "order.html")


def registration(request):
    return render(request, "registration.html")


def recipe_detail(request):
    return render(request, "card3.html")
