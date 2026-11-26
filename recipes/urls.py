from django.urls import path
from django.views.generic import TemplateView

# Пока страницы статичные: на следующих шагах TemplateView заменим настоящими вьюхами

urlpatterns = [
    path("", TemplateView.as_view(template_name="index.html"), name="home"),
    path("login/", TemplateView.as_view(template_name="auth.html"), name="login"),
    path("register/", TemplateView.as_view(template_name="registration.html"), name="register"),
    path("lk/", TemplateView.as_view(template_name="lk.html"), name="lk"),
    path("order/", TemplateView.as_view(template_name="order.html"), name="order"),
    path("recipe/", TemplateView.as_view(template_name="card3.html"), name="recipe"),
]
