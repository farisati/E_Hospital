# admin_panel/forms.py
from django import forms
from django.contrib.auth.models import User
from patient.models import Billing, Payment
from patient.models import Insurance


class PaymentForm(forms.ModelForm):
    class Meta:
        model = Payment
        fields = ['method', 'transaction_id']

        
class InsuranceForm(forms.ModelForm):
    class Meta:
        model = Insurance
        fields = ['patient', 'provider', 'policy_number', 'coverage_percent','coverage_details', 'expiry_date']

        widgets = {
            'coverage_percent': forms.NumberInput(attrs={'min': 0, 'max': 100}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['patient'].queryset = User.objects.filter(profile__role='patient')

    
class BillingForm(forms.ModelForm):
    class Meta:
        model = Billing
        fields = ['patient', 'description', 'amount']   # ONLY these 3

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields['patient'].queryset = User.objects.filter(profile__role='patient')
