import string

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.db.models import Avg, Count, Q
from django.urls import reverse


class BookQuerySet(models.QuerySet):
    def with_popularity(self):
        return self.annotate(
            issue_count=Count("borrow_records", distinct=True),
            avg_rating=Avg("reviews__rating", filter=Q(reviews__is_public=True)),
            review_count=Count("reviews", filter=Q(reviews__is_public=True), distinct=True),
        )


class Book(models.Model):
    """A physical or digital catalog item tracked by library stock."""

    class Genre(models.TextChoices):
        FICTION = "Fiction", "Fiction"
        SCI_FI = "Science Fiction", "Science Fiction"
        COMPUTER_SCIENCE = "Computer Science", "Computer Science"
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
    external_cover_url = models.URLField(blank=True)
    total_stock = models.PositiveIntegerField(default=1)
    available_stock = models.PositiveIntegerField(default=1)
    publication_year = models.PositiveIntegerField(blank=True, null=True)
    publisher = models.CharField(max_length=160, blank=True)
    ebook_url = models.URLField(blank=True)
    ebook_provider_label = models.CharField(max_length=120, blank=True)
    pdf_url = models.URLField(blank=True)
    source_url = models.URLField(blank=True)
    digital_copy_format = models.CharField(max_length=40, blank=True, default="Web")
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

    @property
    def cover_url(self):
        if self.cover_image:
            return self.cover_image.url
        return self.external_cover_url

    @property
    def average_rating_value(self):
        if hasattr(self, "avg_rating") and self.avg_rating is not None:
            return round(self.avg_rating, 1)
        average = self.reviews.filter(is_public=True).aggregate(avg=Avg("rating"))["avg"]
        return round(average, 1) if average else None

    def issue_copy(self):
        if not self.is_available:
            raise ValidationError("No available copies for this book.")
        self.available_stock -= 1
        self.save(update_fields=["available_stock", "updated_at"])

    def return_copy(self):
        if self.available_stock < self.total_stock:
            self.available_stock += 1
            self.save(update_fields=["available_stock", "updated_at"])


class BookReview(models.Model):
    """Member-submitted rating and review for a catalog item."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="book_reviews",
    )
    book = models.ForeignKey(Book, on_delete=models.CASCADE, related_name="reviews")
    rating = models.PositiveSmallIntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])
    title = models.CharField(max_length=120)
    body = models.TextField()
    is_public = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(fields=["user", "book"], name="unique_review_per_book_user"),
        ]

    def __str__(self):
        return f"{self.rating}/5 for {self.book.title} by {self.user}"

    @property
    def star_display(self):
        return "★" * self.rating + "☆" * (5 - self.rating)
