from django.db import models
from django.conf import settings
from django.utils import timezone
from django.db import models
from django.contrib.auth.models import User
from django.contrib.auth import get_user_model


User = settings.AUTH_USER_MODEL

APPOINTMENT_STATUS = (
    ('pending', 'Pending'),
    ('confirmed', 'Confirmed'),
    ('cancelled', 'Cancelled'),
    ('completed', 'Completed'),
)


class Appointment(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='appointments')
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='doctor_appointments')
    date = models.DateField()
    time = models.TimeField()
    reason = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=APPOINTMENT_STATUS, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-time']

    def __str__(self):
        return f"{self.patient} — {self.date} {self.time} ({self.status})"


class MedicalRecord(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medical_records')
    doctor = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='issued_records')
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True)
    diagnosis = models.CharField(max_length=255, blank=True)
    notes = models.TextField(blank=True)
    allergies = models.TextField(blank=True)
    medications = models.TextField(blank=True)
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Record: {self.patient} — {self.diagnosis or 'No diagnosis'}"


class Prescription(models.Model):
    record = models.ForeignKey(MedicalRecord, on_delete=models.CASCADE, related_name='prescriptions')
    medication = models.TextField()
    instructions = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Prescription for {self.record.patient} ({self.created_at.date()})"





class HealthResource(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()
    published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title





class Insurance(models.Model):
    patient = models.OneToOneField(User, on_delete=models.CASCADE)
    provider = models.CharField(max_length=100)
    policy_number = models.CharField(max_length=100)
    coverage_details = models.TextField()
    coverage_percent = models.PositiveIntegerField(default=0)
    expiry_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.provider} - {self.policy_number}"


class Billing(models.Model):
    patient = models.ForeignKey(User, on_delete=models.CASCADE)
    description = models.CharField(max_length=255)
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    insurance = models.ForeignKey(Insurance, on_delete=models.SET_NULL, null=True, blank=True)
    insurance_covered_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    amount_due = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    STATUS_CHOICES = [
        ('unpaid', 'Unpaid'),
        ('paid', 'Paid'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='unpaid')

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Bill {self.id} - {self.patient.username}"

    def calculate_due(self):
        
        if self.insurance and getattr(self.insurance, "coverage_percent", None) is not None:
            self.insurance_covered_amount = (self.amount * self.insurance.coverage_percent) / 100
            self.amount_due = self.amount - self.insurance_covered_amount
        else:
            self.insurance_covered_amount = 0
            self.amount_due = self.amount

    def save(self, *args, **kwargs):
        self.calculate_due()
        super().save(*args, **kwargs)


class Payment(models.Model):
    billing = models.ForeignKey(
        Billing,
        on_delete=models.CASCADE,
        related_name="payments",
        null=True,
        blank=True
    )
    patient = models.ForeignKey(User, on_delete=models.CASCADE, related_name="patient_payments")
    amount = models.DecimalField(max_digits=10, decimal_places=2)

    METHOD_CHOICES = [
        ('online', 'Online'),
        ('upi', 'UPI'),
        ('card', 'Card'),
        ('cash', 'Cash'),
    ]
    method = models.CharField(max_length=20, choices=METHOD_CHOICES)

    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    paid_at = models.DateTimeField(auto_now_add=True)

    STATUS_CHOICES = [
        ('paid', 'Paid'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
    ]
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')

    def __str__(self):
        return f"Payment #{self.id} - {self.patient.username}"
    
User = get_user_model()

class HealthCategory(models.Model):
    name = models.CharField(max_length=100)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class HealthResource(models.Model):
    RESOURCE_TYPES = (
        ('article', 'Article'),
        ('tip', 'Health Tip'),
    ) 

    title = models.CharField(max_length=200)
    category = models.ForeignKey(HealthCategory,on_delete=models.CASCADE,related_name="resources")
    resource_type = models.CharField(max_length=20,choices=RESOURCE_TYPES)
    content = models.TextField(help_text="Article content or Health tip text")
    is_active = models.BooleanField(default=True)
    created_by = models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title