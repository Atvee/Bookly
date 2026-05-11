from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model

from catalog.models import Book, BookReview


class BookModelTests(TestCase):
    def test_category_is_derived_from_title(self):
        book = Book.objects.create(
            title="  42 Stories",
            author="Reader",
            isbn="123",
            description="A test book.",
            genre=Book.Genre.FICTION,
        )

        self.assertEqual(book.category, "S")


class BookListTests(TestCase):
    def setUp(self):
        Book.objects.create(
            title="Ocean of Stars",
            author="A. Writer",
            isbn="456",
            description="A science book.",
            genre=Book.Genre.SCIENCE,
            total_stock=2,
            available_stock=2,
        )

    def test_search_by_title(self):
        response = self.client.get(reverse("catalog:book_list"), {"q": "Ocean"})

        self.assertContains(response, "Ocean of Stars")


class BookReviewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username="reader", password="MemberPass123!")
        self.book = Book.objects.create(
            title="Reviewed Book",
            author="A. Critic",
            isbn="REV-1",
            description="A test book.",
            genre=Book.Genre.FICTION,
        )

    def test_authenticated_user_can_review_book(self):
        self.client.login(username="reader", password="MemberPass123!")
        response = self.client.post(
            reverse("catalog:book_review", args=[self.book.pk]),
            {"rating": 5, "title": "Excellent", "body": "A thoughtful read."},
        )

        self.assertRedirects(response, self.book.get_absolute_url())
        self.assertEqual(BookReview.objects.get(book=self.book, user=self.user).rating, 5)
