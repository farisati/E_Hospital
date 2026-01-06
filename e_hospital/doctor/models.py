from django.db import models
from django.conf import settings
from django.utils import timezone



User = settings.AUTH_USER_MODEL


class DoctorProfile(models.Model):
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='doctor_profile')
    department = models.CharField(max_length=255,null=True,blank=True)
    qualifications = models.CharField(max_length=255, blank=True)
    bio = models.TextField(blank=True)
    clinic_address = models.CharField(max_length=255, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    profile_image = models.ImageField(
        upload_to="doctor_profiles/",
        null=True,
        blank=True
    )


    def __str__(self):
        return f"Dr. { self.user.username}"


WEEK_DAYS = (
    (0, 'Monday'),
    (1, 'Tuesday'),
    (2, 'Wednesday'),
    (3, 'Thursday'),
    (4, 'Friday'),
    (5, 'Saturday'),
    (6, 'Sunday'),
)

class Availability(models.Model):
   
    doctor = models.ForeignKey(User, on_delete=models.CASCADE, related_name='availabilities')
    day_of_week = models.IntegerField(choices=WEEK_DAYS)
    start_time = models.TimeField()
    end_time = models.TimeField()
    slot_duration_minutes = models.PositiveIntegerField(default=15)  # e.g., 15-minute slots

    class Meta:
        ordering = ['doctor', 'day_of_week', 'start_time']
        unique_together = ('doctor', 'day_of_week', 'start_time', 'end_time')

    def __str__(self):
        return f"{self.doctor.username} - {self.get_day_of_week_display()} {self.start_time}-{self.end_time}"


