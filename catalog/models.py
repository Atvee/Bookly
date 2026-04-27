import string

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Count
from django.urls import reverse


class BookQuerySet(models.QuerySet):
    def with_popularity(self):
        return self.annotate(issue_count=Count("borrow_records", distinct=True))


class Book(models.Model):
    """A physical or digital catalog item tracked by library stock."""

    class Genre(models.TextChoices):
        FICTION = "Fiction", "Fiction"
        SCIENCE = "Science", "Science"
        HISTORY = "History", "History"
        TECHNOLOGY = "Technology", "Technology"
        BIOGRAPHY = "Biography", "Biography"
        PHILOSOPHY = "Philosophy", "Philosophy"
        ART = "Art", "Art"
        CHILDREN = "Children", "Children"
        REFERENCE = "Reference", "Reference"
        OTHER = "Other", "Other"

    CATEGORY_CHOICES = [(letter, letter) for letter in string.ascii_uppercase]

    title = models.CharField(max_length=255, db_index=True)
    author = models.CharField(max_length=255, db_index=True)
    isbn = models.CharField("ISBN", max_length=20, unique=True)
    description = models.TextField()
    genre = models.CharField(max_length=40, choices=Genre.choices, db_index=True)
    category = models.CharField(
        max_length=1,
        choices=CATEGORY_CHOICES,
        blank=True,
        db_index=True,
        help_text="A-Z classification, auto-filled from the title when blank.",
    )
    cover_image = models.ImageField(upload_to="covers/", blank=True, null=True)
    total_stock = models.PositiveIntegerField(default=1)
    available_stock = models.PositiveIntegerField(default=1)
    publication_year = models.PositiveIntegerField(blank=True, null=True)
    publisher = models.CharField(max_length=160, blank=True)
    ebook_url = models.URLField(blank=True)
    ebook_provider_label = models.CharField(max_length=120, blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="created_books",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = BookQuerySet.as_manager()

    class Meta:
        ordering = ["title", "author"]
        indexes = [
            models.Index(fields=["title", "author"]),
            models.Index(fields=["genre", "category"]),
        ]

    def __str__(self):
        return f"{self.title} by {self.author}"

    def clean(self):
        if self.available_stock > self.total_stock:
            raise ValidationError("Available stock cannot exceed total stock.")

    def save(self, *args, **kwargs):
        if not self.category:
            self.category = self._derive_category()
        if self.available_stock > self.total_stock:
            self.available_stock = self.total_stock
        super().save(*args, **kwargs)

    def _derive_category(self):
        for char in self.title.upper():
            if char in string.ascii_uppercase:
                return char
        return "A"

    def get_absolute_url(self):
        return reverse("catalog:book_detail", kwargs={"pk": self.pk})

    @property
    def is_available(self):
        return self.available_stock > 0

    @property
    def status_label(self):
        if self.is_available:
            return f"{self.available_stock} available"
        return "Waitlist open"

    def issue_copy(self):
        if not self.is_available:
            raise ValidationError("No available copies for this book.")
        self.available_stock -= 1
        self.save(update_fields=["available_stock", "updated_at"])

    def return_copy(self):
        if self.available_stock < self.total_stock:
            self.available_stock += 1
            self.save(update_fields=["available_stock", "updated_at"])
