from django.contrib import admin

from catalog.models import Book


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
        ("Digital access", {"fields": ("ebook_url", "ebook_provider_label")}),
        ("Media", {"fields": ("cover_image",)}),
        ("Audit", {"fields": ("created_by", "created_at", "updated_at")}),
    )
