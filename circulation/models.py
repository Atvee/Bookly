from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.db.models import Q
from django.urls import reverse
from django.utils import timezone


def default_due_date():
    return timezone.localdate() + timedelta(days=settings.LIBRARY_LOAN_DAYS)


class BorrowRecord(models.Model):
    """A book checkout lifecycle, including return state and fines."""

    class Status(models.TextChoices):
        BORROWED = "BORROWED", "Borrowed"
        RETURNED = "RETURNED", "Returned"
        LOST = "LOST", "Lost"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="borrow_records",
    )
    book = models.ForeignKey(
        "catalog.Book",
        on_delete=models.PROTECT,
        related_name="borrow_records",
    )
    issued_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="issued_records",
    )
    issue_date = models.DateField(default=timezone.localdate)
    due_date = models.DateField(default=default_due_date)
    return_date = models.DateField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.BORROWED)
    fine_paid = models.BooleanField(default=False)
    notes = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-issue_date", "-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "book"],
                condition=Q(return_date__isnull=True, status="BORROWED"),
                name="unique_active_book_per_user",
            )
        ]
        indexes = [
            models.Index(fields=["status", "due_date"]),
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"{self.book.title} issued to {self.user}"

    def get_absolute_url(self):
        return reverse("circulation:history")

    @property
    def is_active(self):
        return self.status == self.Status.BORROWED and self.return_date is None

    @property
    def overdue_days(self):
        end_date = self.return_date or timezone.localdate()
        return max((end_date - self.due_date).days, 0)

    @property
    def is_overdue(self):
        return self.overdue_days > 0 and self.is_active

    @property
    def fine_amount(self):
        rate = Decimal(str(settings.LIBRARY_FINE_RATE_PER_DAY))
        return self.overdue_days * rate

    @property
    def fine_due(self):
        if self.fine_paid:
            return Decimal("0.00")
        return self.fine_amount

    def return_book(self):
        if not self.is_active:
            return
        self.return_date = timezone.localdate()
        self.status = self.Status.RETURNED
        self.book.return_copy()
        self.save(update_fields=["return_date", "status", "updated_at"])
        notify_waitlist_for_book(self.book)


class BookRequest(models.Model):
    """A member request for an unavailable or not-yet-stocked book."""

    class Status(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        NOTIFIED = "NOTIFIED", "Notified"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="book_requests",
    )
    book = models.ForeignKey(
        "catalog.Book",
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="requests",
    )
    requested_title = models.CharField(max_length=255, blank=True)
    requested_author = models.CharField(max_length=255, blank=True)
    genre = models.CharField(max_length=40, blank=True)
    note = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    admin_notes = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="reviewed_book_requests",
    )
    reviewed_at = models.DateTimeField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["status", "created_at"])]

    def __str__(self):
        return f"{self.display_title} requested by {self.user}"

    @property
    def display_title(self):
        if self.book:
            return self.book.title
        return self.requested_title or "Untitled request"


class Notification(models.Model):
    """Simple in-app notifications for library events."""

    class Kind(models.TextChoices):
        INFO = "INFO", "Info"
        REQUEST = "REQUEST", "Request"
        RETURN = "RETURN", "Return"
        FINE = "FINE", "Fine"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    kind = models.CharField(max_length=20, choices=Kind.choices, default=Kind.INFO)
    message = models.CharField(max_length=255)
    link = models.CharField(max_length=255, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["user", "is_read", "created_at"])]

    def __str__(self):
        return self.message


def notify_waitlist_for_book(book):
    """Notify approved/pending requesters when stock becomes available."""
    if book.available_stock <= 0:
        return

    requests = BookRequest.objects.filter(
        book=book,
        status__in=[BookRequest.Status.PENDING, BookRequest.Status.APPROVED],
    ).select_related("user", "book")
    for book_request in requests:
        Notification.objects.get_or_create(
            user=book_request.user,
            kind=Notification.Kind.REQUEST,
            message=f"{book.title} is available now.",
            link=book.get_absolute_url(),
        )
        book_request.status = BookRequest.Status.NOTIFIED
        book_request.save(update_fields=["status", "updated_at"])
