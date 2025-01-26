from django.contrib.auth.backends import ModelBackend
from accounts.models import CustomUser  # Import your CustomUser model
from django.core.exceptions import ObjectDoesNotExist


class EmailAuthBackend(ModelBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        try:
            # Authenticate using the custom user model (CustomUser)
            # Assuming email is used as the identifier
            user = CustomUser.objects.get(email=username)
        except ObjectDoesNotExist:
            return None

        if user.check_password(password):
            return user
        return None
