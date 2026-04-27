from django.contrib import admin

from accounts.models import Profile


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "role", "library_id", "phone", "joined_at")
    list_filter = ("role", "joined_at")
    search_fields = ("user__username", "user__email", "library_id", "phone")
