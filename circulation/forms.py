from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone

from accounts.permissions import can_manage_library
from catalog.models import Book
from circulation.models import BookRequest, BorrowRecord, default_due_date


class BorrowBookForm(forms.ModelForm):
    member = forms.ModelChoiceField(
        queryset=get_user_model().objects.none(),
        required=False,
        label="Member",
    )

    class Meta:
        model = BorrowRecord
        fields = ("member", "due_date", "notes")
        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
        }

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
        self.fields["due_date"].initial = default_due_date()
        self.fields["due_date"].help_text = f"Default loan window is {settings.LIBRARY_LOAN_DAYS} days."
        if user and can_manage_library(user):
            self.fields["member"].queryset = get_user_model().objects.filter(is_active=True).order_by(
                "first_name",
                "username",
            )
        else:
            self.fields.pop("member")

    def clean_due_date(self):
        due_date = self.cleaned_data["due_date"]
        if due_date < timezone.localdate():
            raise forms.ValidationError("Due date cannot be in the past.")
        return due_date

    def checkout_user(self):
        member = self.cleaned_data.get("member")
        return member or self.user


class BookRequestForm(forms.ModelForm):
    class Meta:
        model = BookRequest
        fields = ("requested_title", "requested_author", "genre", "note")
        widgets = {"note": forms.Textarea(attrs={"rows": 4})}

    def __init__(self, *args, book=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.book = book
        if book:
            self.fields["requested_title"].initial = book.title
            self.fields["requested_author"].initial = book.author
            self.fields["genre"].initial = book.genre
            self.fields["requested_title"].disabled = True
            self.fields["requested_author"].disabled = True
            self.fields["genre"].disabled = True
        else:
            self.fields["requested_title"].required = True


class RequestReviewForm(forms.ModelForm):
    class Meta:
        model = BookRequest
        fields = ("status", "admin_notes")
        widgets = {"admin_notes": forms.Textarea(attrs={"rows": 4})}
