from django import forms

from catalog.models import Book


class BookForm(forms.ModelForm):
    class Meta:
        model = Book
        fields = (
            "title",
            "author",
            "isbn",
            "description",
            "genre",
            "category",
            "cover_image",
            "total_stock",
            "available_stock",
            "publication_year",
            "publisher",
            "ebook_url",
            "ebook_provider_label",
        )
        widgets = {
            "description": forms.Textarea(attrs={"rows": 5}),
        }


class BookSearchForm(forms.Form):
    SORT_CHOICES = (
        ("popular", "Most borrowed"),
        ("newest", "Newest"),
        ("title", "Title A-Z"),
        ("author", "Author A-Z"),
    )
    AVAILABILITY_CHOICES = (
        ("", "Any availability"),
        ("available", "Available now"),
        ("waitlist", "Waitlist only"),
    )

    q = forms.CharField(required=False, label="Search")
    genre = forms.ChoiceField(required=False, choices=[("", "All genres")] + list(Book.Genre.choices))
    category = forms.ChoiceField(
        required=False,
        choices=[("", "A-Z")] + Book.CATEGORY_CHOICES,
    )
    availability = forms.ChoiceField(required=False, choices=AVAILABILITY_CHOICES)
    sort = forms.ChoiceField(required=False, choices=SORT_CHOICES)
