from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth.views import LogoutView
from django.urls import path

from recipes import views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", views.index, name="home"),
    path("login/", views.login_view, name="login"),
    path("registration/", views.registration, name="registration"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("lk/", views.lk_view, name="lk"),
    path("today-menu/", views.today_menu, name="today_menu"),
    path("order/", views.order, name="order"),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
