from django.db import models
from django.contrib.auth.models import AbstractUser


class User(AbstractUser):
    bio  = models.TextField(null=True, blank=True)
    email = models.EmailField(unique=True)
    photo = models.ImageField(upload_to='users/', null=True, blank=True)

    def __str__(self):
        return self.username
    


class EmailConfirm(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='emails')
    code = models.CharField(max_length=6)


    def __str__(self):
        return self.user
    