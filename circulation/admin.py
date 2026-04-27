from django.contrib import admin

from circulation.models import BookRequest, BorrowRecord, Notification


@admin.register(BorrowRecord)
class BorrowRecordAdmin(admin.ModelAdmin):
    list_display = ("book", "user", "issue_date", "due_date", "return_date", "status", "fine_amount", "fine_paid")
    list_filter = ("status", "fine_paid", "issue_date", "due_date")
    search_fields = ("book__title", "book__isbn", "user__username", "user__email")
    autocomplete_fields = ("book", "user", "issued_by")
    readonly_fields = ("created_at", "updated_at")


@admin.register(BookRequest)
class BookRequestAdmin(admin.ModelAdmin):
    list_display = ("display_title", "user", "status", "reviewed_by", "created_at")
    list_filter = ("status", "created_at", "reviewed_at")
    search_fields = ("requested_title", "requested_author", "book__title", "user__username")
    autocomplete_fields = ("book", "user", "reviewed_by")
    readonly_fields = ("created_at", "updated_at", "reviewed_at")


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ("user", "kind", "message", "is_read", "created_at")
    list_filter = ("kind", "is_read", "created_at")
    search_fields = ("message", "user__username", "user__email")
