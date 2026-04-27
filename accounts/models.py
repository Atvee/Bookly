from django.contrib.auth import get_user_model
from django.db import models


class Profile(models.Model):
    """Extended account metadata for library roles and member identity."""

    class Role(models.TextChoices):
        ADMIN = "ADMIN", "Admin"
        LIBRARIAN = "LIBRARIAN", "Librarian"
        MEMBER = "MEMBER", "Member"

    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.MEMBER,
        db_index=True,
    )
    library_id = models.CharField(max_length=20, unique=True, blank=True, null=True)
    phone = models.CharField(max_length=30, blank=True)
    address = models.CharField(max_length=255, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["user__first_name", "user__username"]

    def __str__(self):
        return f"{self.user.get_full_name() or self.user.username} ({self.get_role_display()})"

    @property
    def can_manage_library(self):
        return self.role in {self.Role.ADMIN, self.Role.LIBRARIAN}
