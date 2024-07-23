from django.contrib.auth.models import AbstractUser
from django.db import models

from accounts.managers import UserManager


# Create your models here.
class User(AbstractUser):
    """
    custom user model
    """
    username = models.CharField(max_length=50, blank=False, null=False, unique=True)
    email = models.EmailField(unique=True)

    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)

    USERNAME_FIELD = "email"

    REQUIRED_FIELDS = []

    objects = UserManager()

    def __str__(self):
        return self.email