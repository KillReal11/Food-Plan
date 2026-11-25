from django.contrib.auth import get_user_model
from django.contrib.auth.backends import ModelBackend


class EmailOrUsernameBackend(ModelBackend):
    """
    Аутентификация:
    - обычные пользователи (is_staff=False) — только по email
    - суперпользователи (is_staff=True) — по email ИЛИ username
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        UserModel = get_user_model()
        login_value = username or kwargs.get("email")
        if login_value is None or password is None:
            return None

        user = None

        try:
            user = UserModel.objects.get(email=login_value)
        except UserModel.DoesNotExist:
            try:
                user = UserModel.objects.get(username=login_value, is_staff=True)
            except UserModel.DoesNotExist:
                UserModel().set_password(password)
                return None

        if user.check_password(password) and self.user_can_authenticate(user):
            return user
        return None
