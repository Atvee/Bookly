from datetime import timedelta

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from catalog.models import Book
from circulation.models import BorrowRecord, PaymentTransaction


class CirculationFlowTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="member", password="MemberPass123!")
        self.book = Book.objects.create(
            title="Checkout Patterns",
            author="A. Librarian",
            isbn="789",
            description="A test book.",
            genre=Book.Genre.REFERENCE,
            total_stock=1,
            available_stock=1,
        )

    def test_issue_book_decrements_stock(self):
        self.client.login(username="member", password="MemberPass123!")
        response = self.client.post(
            reverse("circulation:issue_book", args=[self.book.pk]),
            {"due_date": timezone.localdate() + timedelta(days=7), "notes": ""},
        )

        self.assertRedirects(response, self.book.get_absolute_url())
        self.book.refresh_from_db()
        self.assertEqual(self.book.available_stock, 0)
        self.assertEqual(BorrowRecord.objects.count(), 1)

    def test_fine_amount_uses_overdue_days(self):
        record = BorrowRecord.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.localdate() - timedelta(days=3),
        )

        self.assertEqual(record.overdue_days, 3)
        self.assertEqual(record.fine_amount, 6)

    def test_qr_payment_marks_fine_paid(self):
        record = BorrowRecord.objects.create(
            user=self.user,
            book=self.book,
            due_date=timezone.localdate() - timedelta(days=3),
            return_date=timezone.localdate(),
            status=BorrowRecord.Status.RETURNED,
        )
        payment = PaymentTransaction.objects.create(
            user=self.user,
            borrow_record=record,
            amount=record.fine_due,
            reference="BKLY-TEST-001",
            note="Test dues payment",
        )
        self.client.login(username="member", password="MemberPass123!")
        response = self.client.post(reverse("circulation:payment_confirm", args=[payment.pk]))

        self.assertRedirects(response, reverse("circulation:payments"))
        record.refresh_from_db()
        payment.refresh_from_db()
        self.assertTrue(record.fine_paid)
        self.assertEqual(payment.status, PaymentTransaction.Status.PAID)
