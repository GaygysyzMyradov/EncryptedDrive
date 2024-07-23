from django.contrib.auth.models import BaseUserManager
from django.utils.translation import gettext_lazy


class UserManager(BaseUserManager):
    """
    custom model user manager
    """

    def create_user(self, email, password, **extra_fields):
        """
        creates new user with email and password
        :param email:
        :param password:
        :param extra_fields:
        :return: User
        """
        if not email:
            raise ValueError(gettext_lazy("Please enter your email address"))

        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password, **extra_fields):
        """
        creates and saves super user with given email and password

        :param email:
        :param password:
        :param extra_fields:
        :return:
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError(gettext_lazy("Superuser must be a staff member"))

        if extra_fields.get("is_superuser") is not True:
            raise ValueError(gettext_lazy("superuser must be an admin"))

        user = self.create_user(email, password, **extra_fields)
        return user
