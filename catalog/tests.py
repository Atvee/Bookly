from django.test import TestCase
from django.urls import reverse

from catalog.models import Book


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
