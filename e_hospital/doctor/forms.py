from django import forms
from .models import Availability, DoctorProfile
from django.forms.widgets import TimeInput
from django import forms
from django.contrib.auth.models import User
from accounts.models import Profile
from doctor.models import DoctorProfile
from datetime import datetime, timedelta, time
from .models import Availability
from patient.models import MedicalRecord


class DoctorProfileForm(forms.ModelForm):
    class Meta:
        model = DoctorProfile
        fields = [
            "department",
            "qualifications",
            "phone",
            "clinic_address",
            "bio",
            "profile_image",
        ]


class DoctorCreateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['username', 'first_name', 'email']






class AvailabilityForm(forms.ModelForm):
    class Meta:
        model = Availability
        fields = ["day_of_week", "start_time", "end_time", "slot_duration_minutes"]
        widgets = {
            "start_time": forms.TimeInput(attrs={"type": "time"}),
            "end_time": forms.TimeInput(attrs={"type": "time"}),
            "slot_duration_minutes": forms.NumberInput(attrs={"min": 5}),
        }

    def clean(self):
        cleaned_data = super().clean()
        day = cleaned_data.get("day_of_week")
        start = cleaned_data.get("start_time")
        end = cleaned_data.get("end_time")
        duration = cleaned_data.get("slot_duration_minutes")

        if not day or not start or not end:
            return cleaned_data

        
        if start >= end:
            raise forms.ValidationError("End time must be later than start time.")

        
        total_minutes = (datetime.combine(datetime.today(), end) - 
                         datetime.combine(datetime.today(), start)).total_seconds() / 60

        if duration > total_minutes:
            raise forms.ValidationError("Slot duration cannot be larger than the time range.")

        if total_minutes % duration != 0:
            raise forms.ValidationError(
                f"The selected time range ({int(total_minutes)} min) "
                f"must be divisible by slot duration ({duration} min)."
            )

        
        doctor = self.instance.doctor if self.instance.pk else self.initial.get("doctor")
        

        if doctor:
            qs = Availability.objects.filter(doctor=doctor, day_of_week=day)

            if self.instance.pk:
                qs = qs.exclude(pk=self.instance.pk)

            for avail in qs:
                if (start < avail.end_time and end > avail.start_time):
                    
                    raise forms.ValidationError(
                        f"Overlapping availability exists: {avail.start_time}–{avail.end_time}"
                    )

        return cleaned_data
    
    from django import forms
from patient.models import Prescription

class PrescriptionForm(forms.ModelForm):
    class Meta:
        model = Prescription
        fields = ["medication", "instructions"]
        widgets = {
            "medication": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 4
            }),
            "instructions": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3
            }),
        }


class MedicalRecordForm(forms.ModelForm):
    class Meta:
        model = MedicalRecord
        fields = ["diagnosis", "notes", "allergies", "medications"]
        widgets = {
            "diagnosis": forms.TextInput(attrs={
                "class": "form-control",
                "placeholder": "Diagnosis"
            }),
            "notes": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Doctor notes"
            }),
            "allergies": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 2,
                "placeholder": "Allergies (if any)"
            }),
            "medications": forms.Textarea(attrs={
                "class": "form-control",
                "rows": 3,
                "placeholder": "Current medications"
            }),
        }