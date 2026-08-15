from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Notice


class NoticeForm(forms.ModelForm):
    class Meta:
        model = Notice
        fields = ["title", "description", "category", "image"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "e.g. Water interruption on Elm Street"}),
            "description": forms.Textarea(attrs={"rows": 5, "placeholder": "Add all the useful details..."}),
            "image": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }
        labels = {
            "image": "Photo (optional)",
        }


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"placeholder": "you@example.com"}))
    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={"placeholder": "First name"}))

    class Meta:
        model = User
        fields = ["username", "first_name", "email", "password1", "password2"]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data.get("first_name", "")
        if commit:
            user.save()
        return user