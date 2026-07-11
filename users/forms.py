# Merged from package modules into a single file for simpler navigation.

# --- users/forms/auth.py ---
from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm
from django.contrib.auth.models import User


class UserRegisterForm(UserCreationForm):
    email = forms.EmailField(
        required=False,
        widget=forms.EmailInput(attrs={"class": "form-control", "placeholder": "Email (Optional)"}),
    )

    class Meta:
        model = User
        fields = ("username", "email", "password1", "password2")
        widgets = {
            "username": forms.TextInput(attrs={"class": "form-control", "placeholder": "Username"}),
            "password1": forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"}),
            "password2": forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Confirm Password"}),
        }


class UserLoginForm(AuthenticationForm):
    username = forms.CharField(widget=forms.TextInput(attrs={"class": "form-control", "placeholder": "Username"}))
    password = forms.CharField(widget=forms.PasswordInput(attrs={"class": "form-control", "placeholder": "Password"}))

# --- users/forms/account.py ---
from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Profile


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["bio", "location", "birth_date", "avatar"]
        widgets = {
            "bio": forms.Textarea(attrs={"class": "form-control", "rows": 4}),
            "location": forms.TextInput(attrs={"class": "form-control"}),
            "birth_date": forms.DateInput(attrs={"class": "form-control", "type": "date"}),
            "avatar": forms.FileInput(attrs={"class": "form-control"}),
        }

    def clean_avatar(self):
        avatar = self.cleaned_data.get("avatar")
        if not avatar:
            return avatar
        allowed_types = {"image/jpeg", "image/png", "image/webp"}
        if getattr(avatar, "content_type", "") not in allowed_types:
            raise ValidationError("Avatar must be a JPEG, PNG, or WebP image.")
        if avatar.size > 3 * 1024 * 1024:
            raise ValidationError("Avatar must be 3MB or smaller.")
        return avatar


class UsernameChangeForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ["username"]
        widgets = {
            "username": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "New username",
                    "maxlength": User._meta.get_field("username").max_length,
                }
            ),
        }

    def clean_username(self):
        username = self.cleaned_data["username"].strip()
        if not username:
            raise ValidationError("Username cannot be empty.")
        if User.objects.filter(username__iexact=username).exclude(pk=self.instance.pk).exists():
            raise ValidationError("Username already exists.")
        return username
