from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth import get_user_model

User = get_user_model()

class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=False, label="Email (необязательно)")
    as_translator = forms.BooleanField(required=False, label="Я переводчик")

    class Meta:
        model = User
        fields = ("username", "email")  # пароли берёт из UserCreationForm