from django.contrib import admin
from .models import DoctorProfile, Availability

@admin.register(DoctorProfile)
class DoctorProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'qualifications', 'clinic_address')

@admin.register(Availability)
class AvailabilityAdmin(admin.ModelAdmin):
    list_display = ('doctor', 'day_of_week', 'start_time', 'end_time', 'slot_duration_minutes')
    list_filter = ('doctor', 'day_of_week')

