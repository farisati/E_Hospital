from django.db import models
from django.contrib.auth.models import User
from django.core.validators import RegexValidator




USER_ROLES =(
    ('patient','Patient'),
    ('doctor','Docter'),
    ('admin', 'Admin'),
)

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=USER_ROLES)

    phone = models.CharField(max_length=15, blank=True, null=True,
        validators=[RegexValidator(r'^\+?\d{10,15}$')])
    address = models.CharField(max_length=255, blank=True, null=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
     # Additional for doctor
    specialization = models.CharField(max_length=100, blank=True, null=True)
    experience = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.user.username} - {self.role}"