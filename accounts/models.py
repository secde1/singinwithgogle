from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    phone_number = models.CharField(max_length=13, blank=True, name=True)
    avatar = models.ImageField("аватар", upload_to='/avatars/', blank=True, null=True)

    def __str__(self):
        return self.username
