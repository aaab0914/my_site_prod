# ========================================
# IMPORTS
# ========================================

from django import forms
# forms: Django's form handling framework
# Provides base classes for creating and validating forms

from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
# UserCreationForm: Built-in form for creating new user accounts
# AuthenticationForm: Built-in form for user login (username/password validation)

from django.contrib.auth.models import User
# User: Django's built-in user model

from .models import Profile
# Profile: Custom user profile model from users app


# ========================================
# FORM: USER REGISTRATION
# ========================================

class UserRegisterForm(UserCreationForm):
    """
    Form for user registration.

    Extends Django's built-in UserCreationForm to add an email field
    and custom CSS classes for better styling.

    Attributes:
        email: Custom EmailField with styling and validation
    """

    # Custom email field with styling and required validation
    email = forms.EmailField(
        required=True,  # Email is mandatory for registration
        widget=forms.EmailInput(attrs={
            "class": "form-control",  # Bootstrap-like CSS class for styling
            "placeholder": "Email",  # Placeholder text shown in the input
        }),
    )

    class Meta:
        # Model associated with this form
        model = User
        # Fields to include in the form (order matters for display)
        fields = (
            "username",
            "email",
            'password1',  # First password input
            'password2',  # Confirmation password input
        )
        # Custom widgets for each field to add CSS classes and placeholders
        widgets = {
            "username": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Username",
            }),
            'password1': forms.PasswordInput(attrs={
                "class": "form-control",
                "placeholder": "Password",
            }),
            "password2": forms.PasswordInput(attrs={
                "class": "form-control",
                "placeholder": "Confirm Password",
            })
        }


# ========================================
# FORM: USER LOGIN
# ========================================

class UserLoginForm(AuthenticationForm):
    """
    Form for user login.

    Extends Django's built-in AuthenticationForm to add custom CSS classes
    for username and password fields.

    Attributes:
        username: Custom CharField with styling
        password: Custom CharField with styling
    """

    # Custom username field with styling
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            "class": "form-control",
            "placeholder": "Username",
        })
    )

    # Custom password field with styling
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            "class": "form-control",
            "placeholder": "Password",
        })
    )


# ========================================
# FORM: USER PROFILE
# ========================================

class UserProfileForm(forms.ModelForm):
    """
    Form for editing user profile information.

    Allows users to update their bio, location, birth date, and avatar.

    Attributes:
        Meta: Inner class that defines model and field configuration
    """

    class Meta:
        # Model associated with this form
        model = Profile
        # Fields to include in the form
        fields = ['bio', 'location', 'birth_date', 'avatar']
        # Custom widgets for each field to add CSS classes and input types
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4  # Number of rows for the textarea
            }),
            'location': forms.TextInput(attrs={'class': 'form-control'}),
            'birth_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'  # HTML5 date picker
            }),
            'avatar': forms.FileInput(attrs={'class': 'form-control'}),
        }