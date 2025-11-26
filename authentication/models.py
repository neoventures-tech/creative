from django.contrib.auth.models import AbstractUser

# Create your models here.

class User(AbstractUser):
    class Meta:
        verbose_name = u'Usuário'
        verbose_name_plural = u'Usuários'







