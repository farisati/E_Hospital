from django.contrib import admin
from .models import Insurance, Appointment, MedicalRecord, Prescription, Payment, HealthCategory, HealthResource


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'date', 'time', 'status')
    list_filter = ('status', 'date')
    search_fields = ('patient__username', 'doctor__username')

@admin.register(MedicalRecord)
class MedicalRecordAdmin(admin.ModelAdmin):
    list_display = ('patient', 'doctor', 'diagnosis', 'created_at')
    search_fields = ('patient__username', 'diagnosis')

@admin.register(Prescription)
class PrescriptionAdmin(admin.ModelAdmin):
    list_display = ('record', 'created_at')

@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ('patient', 'amount', 'method', 'paid_at')
    list_filter = ('method',)



@admin.register(Insurance)
class InsuranceAdmin(admin.ModelAdmin):

    # Columns to show in admin insurance list
    list_display = (
        'id',
        'patient',
        'provider',
        'policy_number',
        'coverage_details',
        'expiry_date',
    )

    # Filters on right side
    list_filter = ('provider', 'expiry_date')

    # Search bar (top-right)
    search_fields = (
        'patient__username',
        'policy_number',
        'provider'
    )

    # Field groups in the admin form
    fieldsets = (
        ('Patient Information', {
            'fields': ('patient',)
        }),

        ('Insurance Details', {
            'fields': ('provider', 'policy_number', 'coverage_details', 'expiry_date')
        }),
    )

    # Latest expiry date first
    ordering = ('-expiry_date',)


@admin.register(HealthCategory)
class HealthCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "is_active")
    list_filter = ("is_active",)
    search_fields = ("name",)


@admin.register(HealthResource)
class HealthResourceAdmin(admin.ModelAdmin):
    list_display = (
        "title",
        "category",
        "resource_type",
        "is_active",
        "created_at",
    )
    list_filter = ("resource_type", "category", "is_active")
    search_fields = ("title", "content")