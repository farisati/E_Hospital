from django import forms
from django.utils import timezone
from .models import Appointment
from accounts.models import Profile
from django.contrib.auth.models import User


class AppointmentForm(forms.ModelForm):
    class Meta:
        model = Appointment
        fields = ["doctor", "reason"]   # 🚨 date & time REMOVED
        widgets = {
            "doctor": forms.Select(attrs={"class": "form-control"}),
            "reason": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Describe your problem / reason for appointment"
                }
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Show only doctors
        self.fields["doctor"].queryset = User.objects.filter(
            profile__role="doctor"
        )



class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ["phone", "address"]
