from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.forms import UserCreationForm

from accounts.models import Profile


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=150, required=True)
    last_name = forms.CharField(max_length=150, required=False)
    phone = forms.CharField(max_length=30, required=False)

    class Meta:
        model = get_user_model()
        fields = ("username", "first_name", "last_name", "email", "phone")

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data["first_name"]
        user.last_name = self.cleaned_data.get("last_name", "")
        if commit:
            user.save()
            user.profile.phone = self.cleaned_data.get("phone", "")
            user.profile.save(update_fields=["phone"])
        return user


class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = get_user_model()
        fields = ("first_name", "last_name", "email")


class ProfileUpdateForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ("phone", "address", "avatar")
