
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.core.exceptions import ValidationError

from accounts.models import User


@receiver(pre_save, sender=User)
def restrict_superuser_creation(sender, instance, **kwargs):
    if instance.is_superuser:
        # Check if a superuser already exists
        if User.objects.filter(is_superuser=True).exists() and not instance.pk:
            raise ValidationError('Only one superuser is allowed.')





