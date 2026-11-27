from django.shortcuts import render


def index(request):
    return render(request, "index.html")


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
