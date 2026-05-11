from django.contrib import admin

from catalog.models import Book, BookReview


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "author",
        "isbn",
        "genre",
        "category",
        "available_stock",
        "total_stock",
        "average_rating_value",
        "updated_at",
    )
    list_filter = ("genre", "category", "created_at")
    search_fields = ("title", "author", "isbn", "publisher")
    readonly_fields = ("created_at", "updated_at")
    list_editable = ("available_stock", "total_stock")
    fieldsets = (
        ("Book details", {"fields": ("title", "author", "isbn", "description", "publisher", "publication_year")}),
        ("Classification", {"fields": ("genre", "category")}),
        ("Inventory", {"fields": ("total_stock", "available_stock")}),
        ("Digital access", {"fields": ("ebook_url", "ebook_provider_label", "pdf_url", "source_url", "digital_copy_format")}),
        ("Media", {"fields": ("cover_image", "external_cover_url")}),
        ("Audit", {"fields": ("created_by", "created_at", "updated_at")}),
    )


@admin.register(BookReview)
class BookReviewAdmin(admin.ModelAdmin):
    list_display = ("book", "user", "rating", "title", "is_public", "created_at")
    list_filter = ("rating", "is_public", "created_at")
    search_fields = ("book__title", "user__username", "title", "body")
    autocomplete_fields = ("book", "user")
