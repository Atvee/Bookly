from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from accounts.models import Profile


@receiver(post_save, sender=get_user_model())
def create_or_sync_profile(sender, instance, created, **kwargs):
    """Keep a profile attached to every user account."""
    profile, _ = Profile.objects.get_or_create(user=instance)
    if not profile.library_id:
        profile.library_id = f"LIB-{instance.pk:05d}"
    if instance.is_superuser or instance.is_staff:
        profile.role = Profile.Role.ADMIN
    profile.save(update_fields=["library_id", "role"])
