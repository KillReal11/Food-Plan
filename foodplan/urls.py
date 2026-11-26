from django.contrib import admin
from django.urls import path
from recipes.views import index, personal_account, order, registration, auth, recipe_detail


urlpatterns = [
    path("admin/", admin.site.urls),
    path("", index, name='index'),
    path("registration/", registration, name='registration'),
    path("auth/", auth, name='auth'),
    path("lk/", personal_account, name='lk'),
    path("recipe/", recipe_detail, name='recipe'),
    path("order/", order, name='order'),   
]
