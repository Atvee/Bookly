from urllib.parse import quote_plus

from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Count, Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import CreateView, DeleteView, DetailView, ListView, TemplateView, UpdateView

from accounts.permissions import LibraryStaffRequiredMixin
from catalog.forms import BookForm, BookSearchForm
from catalog.models import Book


class HomeView(TemplateView):
    template_name = "catalog/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        popular = Book.objects.with_popularity().order_by("-issue_count", "-created_at")
        context["featured_books"] = popular.filter(available_stock__gt=0)[:6]
        context["new_books"] = Book.objects.order_by("-created_at")[:6]
        context["genres"] = Book.objects.values("genre").annotate(total=Count("id")).order_by("genre")
        context["categories"] = (
            Book.objects.values("category").annotate(total=Count("id")).order_by("category")[:12]
        )
        return context


class BookListView(ListView):
    model = Book
    template_name = "catalog/book_list.html"
    context_object_name = "books"
    paginate_by = 9

    def get_queryset(self):
        queryset = Book.objects.with_popularity()
        self.search_form = BookSearchForm(self.request.GET)
        if self.search_form.is_valid():
            data = self.search_form.cleaned_data
            query = data.get("q")
            if query:
                queryset = queryset.filter(
                    Q(title__icontains=query)
                    | Q(author__icontains=query)
                    | Q(genre__icontains=query)
                    | Q(isbn__icontains=query)
                )
            if data.get("genre"):
                queryset = queryset.filter(genre=data["genre"])
            if data.get("category"):
                queryset = queryset.filter(category=data["category"])
            if data.get("availability") == "available":
                queryset = queryset.filter(available_stock__gt=0)
            if data.get("availability") == "waitlist":
                queryset = queryset.filter(available_stock=0)
            sort = data.get("sort") or "popular"
        else:
            sort = "popular"

        ordering = {
            "popular": ("-issue_count", "title"),
            "newest": ("-created_at", "title"),
            "title": ("title", "author"),
            "author": ("author", "title"),
        }.get(sort, ("-issue_count", "title"))
        return queryset.order_by(*ordering)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query_params = self.request.GET.copy()
        query_params.pop("page", None)
        context["search_form"] = self.search_form
        context["querystring"] = query_params.urlencode()
        context["active_filters"] = {
            key: value
            for key, value in self.request.GET.items()
            if value and key in {"q", "genre", "category", "availability", "sort"}
        }
        context["genre_counts"] = Book.objects.values("genre").annotate(total=Count("id")).order_by("genre")
        return context


class BookDetailView(DetailView):
    model = Book
    template_name = "catalog/book_detail.html"
    context_object_name = "book"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["recommendations"] = (
            Book.objects.with_popularity()
            .filter(genre=self.object.genre)
            .exclude(pk=self.object.pk)
            .order_by("-issue_count", "title")[:4]
        )
        if self.request.user.is_authenticated:
            from circulation.forms import BorrowBookForm
            from circulation.models import BorrowRecord

            context["borrow_form"] = BorrowBookForm(user=self.request.user)
            context["active_borrow"] = BorrowRecord.objects.filter(
                book=self.object,
                user=self.request.user,
                status=BorrowRecord.Status.BORROWED,
                return_date__isnull=True,
            ).first()
        return context


class BookCreateView(LoginRequiredMixin, LibraryStaffRequiredMixin, CreateView):
    model = Book
    form_class = BookForm
    template_name = "catalog/book_form.html"

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        messages.success(self.request, "Book added to the catalog.")
        return super().form_valid(form)


class BookUpdateView(LoginRequiredMixin, LibraryStaffRequiredMixin, UpdateView):
    model = Book
    form_class = BookForm
    template_name = "catalog/book_form.html"

    def form_valid(self, form):
        messages.success(self.request, "Book updated.")
        return super().form_valid(form)


class BookDeleteView(LoginRequiredMixin, LibraryStaffRequiredMixin, DeleteView):
    model = Book
    template_name = "catalog/book_confirm_delete.html"
    success_url = reverse_lazy("catalog:book_list")

    def form_valid(self, form):
        messages.success(self.request, "Book removed from the catalog.")
        return super().form_valid(form)


class EbookSearchView(DetailView):
    model = Book
    template_name = "catalog/ebook_search.html"
    context_object_name = "book"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        query = quote_plus(f"{self.object.title} {self.object.author}")
        context["legal_sources"] = [
            ("Open Library", f"https://openlibrary.org/search?q={query}"),
            ("Project Gutenberg", f"https://www.gutenberg.org/ebooks/search/?query={query}"),
            ("Internet Archive", f"https://archive.org/search?query={query}"),
            ("WorldCat", f"https://search.worldcat.org/search?q={query}"),
        ]
        return context


class EbookRedirectView(DetailView):
    model = Book

    def get(self, request, *args, **kwargs):
        book = self.get_object()
        if book.ebook_url:
            return redirect(book.ebook_url)
        return redirect("catalog:ebook_search", pk=book.pk)


class BookApiListView(View):
    def get(self, request):
        books = BookListView()
        books.request = request
        queryset = books.get_queryset()[:50]
        return JsonResponse(
            {
                "results": [
                    {
                        "id": book.pk,
                        "title": book.title,
                        "author": book.author,
                        "isbn": book.isbn,
                        "genre": book.genre,
                        "category": book.category,
                        "available_stock": book.available_stock,
                        "total_stock": book.total_stock,
                        "detail_url": request.build_absolute_uri(book.get_absolute_url()),
                    }
                    for book in queryset
                ]
            }
        )


class BookApiDetailView(View):
    def get(self, request, pk):
        book = get_object_or_404(Book, pk=pk)
        return JsonResponse(
            {
                "id": book.pk,
                "title": book.title,
                "author": book.author,
                "isbn": book.isbn,
                "description": book.description,
                "genre": book.genre,
                "category": book.category,
                "available_stock": book.available_stock,
                "total_stock": book.total_stock,
                "cover_url": request.build_absolute_uri(book.cover_image.url) if book.cover_image else "",
            }
        )
