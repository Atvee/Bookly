from django.urls import path

from catalog.views import (
    BookApiDetailView,
    BookApiListView,
    BookCreateView,
    BookDeleteView,
    BookDetailView,
    BookListView,
    BookReviewCreateView,
    BookUpdateView,
    EbookRedirectView,
    EbookSearchView,
    HomeView,
)

app_name = "catalog"

urlpatterns = [
    path("", HomeView.as_view(), name="home"),
    path("books/", BookListView.as_view(), name="book_list"),
    path("books/add/", BookCreateView.as_view(), name="book_add"),
    path("books/<int:pk>/", BookDetailView.as_view(), name="book_detail"),
    path("books/<int:pk>/edit/", BookUpdateView.as_view(), name="book_edit"),
    path("books/<int:pk>/delete/", BookDeleteView.as_view(), name="book_delete"),
    path("books/<int:pk>/reviews/", BookReviewCreateView.as_view(), name="book_review"),
    path("books/<int:pk>/ebooks/", EbookSearchView.as_view(), name="ebook_search"),
    path("books/<int:pk>/ebooks/open/", EbookRedirectView.as_view(), name="ebook_open"),
    path("api/books/", BookApiListView.as_view(), name="api_book_list"),
    path("api/books/<int:pk>/", BookApiDetailView.as_view(), name="api_book_detail"),
]
