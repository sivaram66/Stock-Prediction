from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from .models import UserChances


@receiver(post_save, sender=settings.AUTH_USER_MODEL)
def create_user_chances(sender, instance, created, **kwargs):
    if created:
        UserChances.objects.create(user=instance)
