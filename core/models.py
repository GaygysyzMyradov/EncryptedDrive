# Create your models here.
import random

from django.db import models
from django.utils.text import slugify

from accounts.models import User


class Folder(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    folder_owner = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = self.generate_unique_slug(self.name)

        super(Folder, self).save(*args, **kwargs)

    def generate_unique_slug(self, name):
        slug = slugify(name)
        unique_slug = slug
        suffix = random.randint(1, 9999)
        while Folder.objects.filter(slug=unique_slug).exists():
            unique_slug = f"{slug}-{suffix}"
            suffix += 1
        return unique_slug


class File(models.Model):
    file_owner = models.ForeignKey(User, on_delete=models.CASCADE)
    folder = models.ForeignKey(Folder, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    slug = models.SlugField()
    file = models.FileField(upload_to='files/')
    decrypted = models.BooleanField(default=False)
    decryption_key = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.id:
            self.slug = self.generate_unique_slug(self.name)
        super(File, self).save(*args, **kwargs)

    def generate_unique_slug(self, name):
        slug = slugify(name)
        unique_slug = slug
        suffix = random.randint(1, 9999)
        while File.objects.filter(slug=unique_slug, file_owner=self.file_owner).exists():
            unique_slug = f"{slug}-{suffix}"
            suffix += 1
        return unique_slug

    @property
    def file_size(self):
        if self.file:
            return self.file.size
        return None
