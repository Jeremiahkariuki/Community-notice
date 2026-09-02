from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from .models import Notice, Comment


class MultiFileInput(forms.ClearableFileInput):
    allow_multiple_selected = True


class MultiFileField(forms.FileField):
    """A FileField that accepts and returns a list of uploaded files."""

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultiFileInput(attrs={"multiple": True, "accept": "image/*"}))
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean
        if isinstance(data, (list, tuple)):
            return [single_file_clean(d, initial) for d in data]
        return single_file_clean(data, initial)


class NoticeForm(forms.ModelForm):
    extra_images = MultiFileField(
        required=False,
        label="Additional photos (optional)",
        help_text="You can select multiple photos to add to a gallery on this notice.",
    )

    class Meta:
        model = Notice
        fields = ["title", "description", "category", "priority", "location", "expires_at", "image"]
        widgets = {
            "title": forms.TextInput(attrs={"placeholder": "e.g. Water interruption on Elm Street"}),
            "description": forms.Textarea(attrs={"rows": 5, "placeholder": "Add all the useful details..."}),
            "priority": forms.Select(attrs={"class": "form-select"}),
            "location": forms.TextInput(attrs={"placeholder": "e.g. Elm Street / Riverside Estate"}),
            "expires_at": forms.DateTimeInput(
                attrs={"type": "datetime-local"},
                format="%Y-%m-%dT%H:%M",
            ),
            "image": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }
        labels = {
            "priority": "Urgency Level",
            "expires_at": "Expiration Date & Time (Optional)",
            "image": "Cover photo (optional)",
            "location": "Location (optional)",
        }
        help_texts = {
            "priority": "Selecting 'Emergency Alert 🚨' displays a prominent warning banner at the top of all pages.",
            "expires_at": "Notice will automatically disappear from public listings after this date and time.",
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.pk and self.instance.expires_at:
            self.initial["expires_at"] = self.instance.expires_at.strftime("%Y-%m-%dT%H:%M")


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ["body"]
        widgets = {
            "body": forms.Textarea(
                attrs={"rows": 3, "placeholder": "Add a comment or update...", "maxlength": 1000}
            ),
        }
        labels = {"body": ""}


class SignUpForm(UserCreationForm):
    email = forms.EmailField(required=True, widget=forms.EmailInput(attrs={"placeholder": "you@example.com"}))
    first_name = forms.CharField(max_length=30, required=False, widget=forms.TextInput(attrs={"placeholder": "First name"}))

    class Meta:
        model = User
        fields = ["username", "first_name", "email", "password1", "password2"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["password1"].help_text = ""
        self.fields["password2"].help_text = ""

    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data["email"]
        user.first_name = self.cleaned_data.get("first_name", "")
        if commit:
            user.save()
        return user