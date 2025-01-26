from celery import shared_task
from django.db.models import F
from .models import UserChances


@shared_task
def reset_chances_daily():
    """
    Resets `chances_left` to `total_chances` for all users.
    """
    UserChances.objects.update(chances_left=F('total_chances'))
