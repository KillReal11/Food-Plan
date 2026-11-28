from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError

from .models import Allergen, MealType, MenuType, SubscriptionPlan

User = get_user_model()

MAX_PERSONS = 6


class RegistrationForm(forms.Form):
    name = forms.CharField(label="Имя", max_length=150)
    email = forms.EmailField(label="Email")
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)
    password_confirm = forms.CharField(label="Подтверждение пароля", widget=forms.PasswordInput)

    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exists():
            raise ValidationError("Пользователь с таким email уже зарегистрирован.")
        return email

    def clean(self):
        cleaned = super().clean()
        password = cleaned.get("password")
        confirm = cleaned.get("password_confirm")
        if password and confirm and password != confirm:
            self.add_error("password_confirm", "Пароли не совпадают.")
        elif password:
            candidate = User(email=cleaned.get("email", ""), first_name=cleaned.get("name", ""))
            try:
                validate_password(password, candidate)
            except ValidationError as error:
                self.add_error("password", error)
        return cleaned

    def save(self):
        data = self.cleaned_data
        return User.objects.create_user(
            email=data["email"],
            password=data["password"],
            first_name=data["name"],
        )


class LoginForm(forms.Form):
    email = forms.CharField(label="Email", max_length=254)
    password = forms.CharField(label="Пароль", widget=forms.PasswordInput)

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        self.user = None
        super().__init__(*args, **kwargs)

    def clean(self):
        cleaned = super().clean()
        login_value = (cleaned.get("email") or "").strip()
        password = cleaned.get("password")
        if login_value and password:
            user = authenticate(self.request, username=login_value, password=password)
            if user is None and "@" in login_value and login_value != login_value.lower():
                user = authenticate(self.request, username=login_value.lower(), password=password)
            if user is None:
                raise ValidationError("Неверный email или пароль.")
            self.user = user
        return cleaned


class ProfileForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'email']


    def clean_email(self):
        email = self.cleaned_data["email"].strip().lower()
        if User.objects.filter(email__iexact=email).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Пользователь с таким email уже зарегистрирован.")
        return email

      
class OrderForm(forms.Form):
    menu_type = forms.ModelChoiceField(
        queryset=MenuType.objects.none(),
        to_field_name="slug",
        error_messages={
            "required": "Выберите тип меню.",
            "invalid_choice": "Выберите тип меню из списка.",
        },
    )
    plan = forms.ModelChoiceField(
        queryset=SubscriptionPlan.objects.none(),
        error_messages={
            "required": "Выберите срок подписки.",
            "invalid_choice": "Выберите срок подписки из списка.",
        },
    )
    persons_count = forms.IntegerField(
        min_value=1,
        max_value=MAX_PERSONS,
        error_messages={
            "required": "Укажите количество персон.",
            "invalid": "Количество персон должно быть числом.",
            "min_value": "Минимум одна персона.",
            "max_value": f"Максимум {MAX_PERSONS} персон.",
        },
    )
    allergies = forms.ModelMultipleChoiceField(
        queryset=Allergen.objects.order_by("pk"),
        required=False,
        error_messages={
            "invalid_choice": "Выберите аллергены из списка.",
            "invalid_pk_value": "Выберите аллергены из списка.",
        },
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["menu_type"].queryset = MenuType.objects.filter(slug__isnull=False).order_by(
            "pk"
        )
        self.fields["plan"].queryset = SubscriptionPlan.objects.filter(is_active=True).order_by(
            "duration_months"
        )
        self.meals = list(MealType.objects.all())
        for meal in self.meals:
            self.fields[f"meal_{meal.pk}"] = forms.BooleanField(required=False)
        self.selected_meals = []

    def clean(self):
        cleaned = super().clean()
        self.selected_meals = [meal for meal in self.meals if cleaned.get(f"meal_{meal.pk}")]
        if not self.selected_meals:
            raise ValidationError("Выберите хотя бы один приём пищи.")
        return cleaned
