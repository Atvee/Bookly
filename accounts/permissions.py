from django.contrib.auth.mixins import UserPassesTestMixin


def can_manage_library(user):
    if not user.is_authenticated:
        return False
    if user.is_staff or user.is_superuser:
        return True
    profile = getattr(user, "profile", None)
    return bool(profile and profile.can_manage_library)


class LibraryStaffRequiredMixin(UserPassesTestMixin):
    """Allow admins and librarians to reach operational pages."""

    permission_denied_message = "You need librarian access to manage this area."

    def test_func(self):
        return can_manage_library(self.request.user)
