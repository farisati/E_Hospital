from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from django.contrib.auth.models import User
from django.http import JsonResponse
from functools import wraps

# MODELS
from accounts.models import Profile
from patient.models import Appointment, MedicalRecord, Payment, Billing, Insurance,  HealthCategory, HealthResource
from doctor.models import DoctorProfile, Availability

# FORMS
from .forms import BillingForm, PaymentForm
from doctor.forms import DoctorCreateForm, DoctorProfileForm


# =====================================================
# ADMIN ROLE CHECK DECORATOR
# =====================================================

def admin_required(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect("accounts:login")

            profile = getattr(request.user, "profile", None)

            if not profile or profile.role != "admin":
                messages.error(request, "Access denied.")
                return redirect("accounts:login")

            return view_func(request, *args, **kwargs)
        return wrapper



# =====================================================
# ADMIN DASHBOARD
# =====================================================
@login_required
@admin_required
def dashboard(request):
    total_doctors = Profile.objects.filter(role='doctor').count()
    total_patients = Profile.objects.filter(role='patient').count()
    pending_appts = Appointment.objects.filter(status='pending').count()

    return render(request, "admin_panel/dashboard.html", {
        "total_doctors": total_doctors,
        "total_patients": total_patients,
        "pending_appts": pending_appts,
    })


# =====================================================
# DOCTOR MANAGEMENT
# =====================================================
@login_required
@admin_required
def doctor_list(request):
    doctors = DoctorProfile.objects.select_related("user").all()
    return render(request, "admin_panel/doctors.html", {"doctors": doctors})


@login_required
@admin_required
def doctor_add(request):
    if request.method == "POST":
        user_form = DoctorCreateForm(request.POST)
        profile_form = DoctorProfileForm(request.POST)

        if user_form.is_valid() and profile_form.is_valid():

            # Create User
            user = user_form.save()
            user.set_password("doctor123")
            user.save()

            # Update auto-created Profile
            profile = user.profile
            profile.role = "doctor"
            profile.save()

            # Create Doctor Profile
            doctor_prof = profile_form.save(commit=False)
            doctor_prof.user = user
            doctor_prof.save()

            messages.success(request, "Doctor added successfully!")
            return redirect("admin_panel:doctor_list")

    else:
        user_form = DoctorCreateForm()
        profile_form = DoctorProfileForm()

    return render(request, "admin_panel/doctor_add.html", {
        "user_form": user_form,
        "profile_form": profile_form
    })


@login_required
@admin_required
def doctor_edit(request, doctor_id):
    user = get_object_or_404(User, id=doctor_id)

    doctor_profile, created = DoctorProfile.objects.get_or_create(user=user)

    if request.method == "POST":
        user_form = DoctorCreateForm(request.POST, instance=user)
        profile_form = DoctorProfileForm(request.POST, instance=doctor_profile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            messages.success(request, "Doctor updated successfully!")
            return redirect("admin_panel:doctor_list")

    else:
        user_form = DoctorCreateForm(instance=user)
        profile_form = DoctorProfileForm(instance=doctor_profile)

    return render(request, "admin_panel/doctor_edit.html", {
        "user_form": user_form,
        "profile_form": profile_form,
        "doctor": user
    })


@login_required
@admin_required
def doctor_delete(request, doctor_id):
    user = get_object_or_404(User, id=doctor_id)

    if request.method == "POST":
        user.delete()
        messages.success(request, "Doctor deleted successfully!")
        return redirect("admin_panel:doctor_list")

    return render(request, "admin_panel/confirm_delete.html", {
        "object": user,
        "type": "Doctor"
    })


# =====================================================
# PATIENT MANAGEMENT
# =====================================================
@login_required
@admin_required
def patient_list(request):
    patients = Profile.objects.filter(role='patient')
    return render(request, "admin_panel/patients.html", {"patients": patients})


@login_required
@admin_required
def patient_add(request):
    if request.method == "POST":
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password") or "patient123"
        phone = request.POST.get("phone")
        address = request.POST.get("address")

        # Validation
        if User.objects.filter(username=username).exists():
            messages.error(request, "Username already exists.")
            return redirect("admin_panel:patient_add")

        if email and User.objects.filter(email=email).exists():
            messages.error(request, "Email already exists.")
            return redirect("admin_panel:patient_add")

        # Create User
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

        # Update Profile
        profile = user.profile
        profile.role = "patient"
        profile.phone = phone
        profile.address = address
        profile.save()

        messages.success(request, "Patient created successfully!")
        return redirect("admin_panel:patient_list")

    return render(request, "admin_panel/patient_add.html")


@login_required
@admin_required
def patient_edit(request, patient_id):
    profile = get_object_or_404(Profile, user_id=patient_id, role="patient")

    if request.method == "POST":
        profile.phone = request.POST.get("phone")
        profile.address = request.POST.get("address")
        profile.save()

        profile.user.email = request.POST.get("email")
        profile.user.save()

        messages.success(request, "Patient updated successfully!")
        return redirect("admin_panel:patient_list")

    return render(request, "admin/patient_edit.html", {"profile": profile})


@login_required
@admin_required
def patient_deactivate(request, patient_id):
    user = get_object_or_404(User, id=patient_id)

    if request.method == "POST":
        user.is_active = False
        user.save()
        messages.success(request, "Patient deactivated successfully!")
        return redirect("admin_panel:patient_list")

    return render(request, "admin_panel/confirm_delete.html", {
        "object": user,
        "type": "Deactivate Patient"
    })


@login_required
@admin_required
def patient_activate(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.is_active = True
    user.save()
    messages.success(request, "Patient activated successfully.")
    return redirect("admin_panel:patient_list")


@login_required
@admin_required
def patient_view(request, patient_id):
    profile = get_object_or_404(Profile, user__id=patient_id)

    appointments = Appointment.objects.filter(patient=profile.user)
    medical_records = MedicalRecord.objects.filter(patient=profile.user)
    bills = Billing.objects.filter(patient=profile.user)
    payments = Payment.objects.filter(patient=profile.user)
    insurance = Insurance.objects.filter(patient=profile.user).first()

    context = {
        "profile": profile,
        "appointments": appointments,
        "medical_records": medical_records,
        "bills": bills,
        "payments": payments,
        "insurance": insurance,
    }

    return render(request, "admin_panel/patient_view.html", context)




# =====================================================
# APPOINTMENTS MANAGEMENT
# =====================================================
@login_required
@admin_required
def appointment_list(request):
    pending = Appointment.objects.filter(status="pending").order_by("date", "time")
    confirmed = Appointment.objects.filter(status="confirmed").order_by("date", "time")
    completed = Appointment.objects.filter(status="completed").order_by("-date")

    return render(request, "admin_panel/appointments.html", {
        "pending": pending,
        "confirmed": confirmed,
        "completed": completed,
    })


@login_required
@admin_required
def approve_appointment(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "approve":
            appt.status = "confirmed"
            appt.doctor = appt.doctor 
            messages.success(request, "Appointment Approved!")
        elif action == "reject":
            appt.status = "cancelled"
            messages.error(request, "Appointment Rejected!")

        appt.save()
        return redirect("admin_panel:appointment_list")

    return render(request, "admin_panel/approve_appointment.html", {"appointment": appt})


@login_required
@admin_required
def appointment_detail(request, pk):
    appt = get_object_or_404(Appointment, pk=pk)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "approve":
            appt.status = "confirmed"
            appt.save()
            messages.success(request, "Appointment approved")

        elif action == "reject":
            appt.status = "cancelled"
            appt.save()
            messages.warning(request, "Appointment rejected")

        elif action == "complete":
            appt.status = "completed"
            appt.save()
            messages.success(request, "Appointment marked completed")

        return redirect("admin_panel:appointment_list")

    return render(request, "admin_panel/appointment_detail.html", {
        "appt": appt
    })


# =====================================================
# BILLING MANAGEMENT
# =====================================================
@login_required
@admin_required
def billing_list(request):
    q = request.GET.get('q', '')
    status = request.GET.get('status', '')

    bills = Billing.objects.select_related('patient').order_by('-created_at')

    if q:
        bills = bills.filter(
            Q(description__icontains=q) |
            Q(patient__username__icontains=q) |
            Q(patient__first_name__icontains=q)
        )

    if status:
        bills = bills.filter(status=status)

    return render(request, "admin_panel/billing_list.html", {
        "bills": bills,
        "q": q,
        "status": status,
        "today": timezone.now().date()
    })


@login_required
@admin_required
def billing_create(request):
    if request.method == 'POST':
        form = BillingForm(request.POST)

        if form.is_valid():
            bill = form.save(commit=False)

            # Insurance
            insurance = Insurance.objects.filter(patient=bill.patient).first()

            if insurance and (not insurance.expiry_date or insurance.expiry_date >= timezone.now().date()):
                bill.insurance = insurance
                bill.insurance_covered_amount = (bill.amount * insurance.coverage_percent) / 100
                bill.amount_due = bill.amount - bill.insurance_covered_amount
            else:
                bill.insurance = None
                bill.insurance_covered_amount = 0
                bill.amount_due = bill.amount

            bill.status = "unpaid"
            bill.save()

            messages.success(request, f"Bill #{bill.id} created successfully!")
            return redirect('admin_panel:billing_list')

    else:
        form = BillingForm()

    return render(request, "admin_panel/billing_form.html", {"form": form})


@login_required
@admin_required
def billing_edit(request, pk):
    bill = get_object_or_404(Billing, pk=pk)

    if request.method == 'POST':
        form = BillingForm(request.POST, instance=bill)
        if form.is_valid():
            bill = form.save(commit=False)

            insurance = Insurance.objects.filter(patient=bill.patient).first()

            if insurance:
                bill.insurance = insurance
                bill.insurance_covered_amount = (bill.amount * insurance.coverage_percent) / 100
                bill.amount_due = bill.amount - bill.insurance_covered_amount
            else:
                bill.insurance = None
                bill.insurance_covered_amount = 0
                bill.amount_due = bill.amount

            bill.save()
            messages.success(request, "Bill updated successfully.")
            return redirect('admin_panel:billing_list')

    else:
        form = BillingForm(instance=bill)

    return render(request, "admin_panel/billing_form.html", {
        "form": form,
        "edit": True,
        "bill": bill
    })


@login_required
@admin_required
def billing_delete(request, pk):
    bill = get_object_or_404(Billing, pk=pk)

    if request.method == "POST":
        bill.delete()
        messages.success(request, "Bill deleted.")
        return redirect('admin_panel:billing_list')

    return render(request, "admin_panel/confirm_delete.html", {
        "object": bill,
        "type": "Bill"
    })


# =====================================================
# PAYMENT
# =====================================================
@login_required
@admin_required
def payments(request):
    pays = Payment.objects.all().order_by('-paid_at')
    return render(request, "admin_panel/payments.html", {"payments": pays})


@login_required
@admin_required
def payment_create(request, billing_pk=None):
    bill = None
    initial = {}

    if billing_pk:
        bill = get_object_or_404(Billing, pk=billing_pk)
        initial['amount'] = bill.amount_due

    if request.method == 'POST':
        form = PaymentForm(request.POST)

        if form.is_valid():
            payment = form.save(commit=False)

            if bill:
                payment.billing = bill
                payment.patient = bill.patient
                payment.amount = bill.amount_due
                payment.save()

                bill.status = 'paid'
                bill.amount_due = 0
                bill.save()

                messages.success(request, "Full payment recorded. Bill marked as PAID.")
                return redirect('admin_panel:billing_list')

    else:
        form = PaymentForm(initial=initial)

    return render(request, "admin_panel/payment_form.html", {
        "form": form,
        "bill": bill
    })


# =====================================================
# INSURANCE MANAGEMENT
# =====================================================
@login_required
@admin_required
def insurance_list(request):
    insurances = Insurance.objects.select_related("patient").all()
    return render(request, 'admin_panel/insurance_list.html', {'insurances': insurances})


@login_required
@admin_required
def insurance_add(request):
    insured_patients = Insurance.objects.values_list("patient_id", flat=True)
    users = User.objects.filter(profile__role="patient", is_active=True).exclude(id__in=insured_patients)

    if request.method == "POST":
        patient_id = request.POST.get("patient")

        if Insurance.objects.filter(patient_id=patient_id).exists():
            messages.error(request, "This patient already has an insurance record.")
            return redirect('admin_panel:insurance_list')

        Insurance.objects.create(
            patient_id=patient_id,
            provider=request.POST.get("provider"),
            policy_number=request.POST.get("policy_number"),
            coverage_percent=int(request.POST.get("coverage_percent") or 0),
            coverage_details=request.POST.get("coverage_details"),
            expiry_date=request.POST.get("expiry_date")
        )

        messages.success(request, "Insurance added successfully.")
        return redirect('admin_panel:insurance_list')

    return render(request, 'admin_panel/insurance_add.html', {'users': users})


@login_required
@admin_required
def insurance_edit(request, id):
    insurance = get_object_or_404(Insurance, id=id)

    if request.method == "POST":
        patient_id = request.POST.get("patient")

        if Insurance.objects.exclude(id=id).filter(patient_id=patient_id).exists():
            messages.error(request, "Another insurance record already exists for this patient.")
            return redirect('admin_panel:insurance_list')

        insurance.provider = request.POST.get("provider")
        insurance.policy_number = request.POST.get("policy_number")
        insurance.coverage_percent = int(request.POST.get("coverage_percent") or 0)
        insurance.coverage_details = request.POST.get("coverage_details")
        insurance.expiry_date = request.POST.get("expiry_date")
        insurance.save()

        messages.success(request, "Insurance updated successfully.")
        return redirect('admin_panel:insurance_list')

    users = User.objects.all()

    return render(request, 'admin_panel/insurance_edit.html', {
        'insurance': insurance,
        'users': users
    })


@login_required
@admin_required
def insurance_delete(request, id):
    insurance = get_object_or_404(Insurance, id=id)

    if request.method == "POST":
        insurance.delete()
        messages.success(request, "Insurance deleted successfully.")
        return redirect('admin_panel:insurance_list')

    return render(request, "admin_panel/confirm_delete.html", {
        "object": insurance,
        "type": "Insurance"
    })


@login_required
@admin_required
def get_insurance(request, patient_id):
    insurance = Insurance.objects.filter(patient_id=patient_id).first()

    if insurance:
        return JsonResponse({
            "has_insurance": True,
            "provider": insurance.provider,  
            "coverage_percent": insurance.coverage_percent
        })

    return JsonResponse({"has_insurance": False})


# =====================================================
# HEALTH CATEGORIES MANAGEMENT
# =====================================================

@login_required
@admin_required
def health_category_list(request):
    """
    List all health categories
    """
    categories = HealthCategory.objects.all()
    return render(
        request,
        "admin_panel/health_category_list.html",
        {"categories": categories}
    )


@login_required
@admin_required
def health_category_add(request):
    """
    Add a new health category
    """
    if request.method == "POST":
        name = request.POST.get("name")

        if name:
            HealthCategory.objects.create(
                name=name,
                is_active=True
            )
            messages.success(request, "Health category added successfully.")
            return redirect("admin_panel:admin_health_categories")

        messages.error(request, "Category name is required.")

    return render(request, "admin_panel/health_category_form.html")


@login_required
@admin_required
def health_category_toggle(request, pk):
    """
    Activate / Deactivate a health category
    """
    category = get_object_or_404(HealthCategory, pk=pk)
    category.is_active = not category.is_active
    category.save()

    messages.success(
        request,
        f"Category {'activated' if category.is_active else 'deactivated'} successfully."
    )

    return redirect("admin_panel:admin_health_categories")


# =====================================================
# HEALTH RESOURCES MANAGEMENT
# =====================================================

@login_required
@admin_required
def health_resource_list(request):
    """
    List all health resources
    """
    resources = HealthResource.objects.select_related("category").order_by("-id")
    return render(
        request,
        "admin_panel/health_resource_list.html",
        {"resources": resources}
    )


@login_required
@admin_required
def health_resource_add(request):
    """
    Add a new health resource
    """
    categories = HealthCategory.objects.filter(is_active=True)

    if request.method == "POST":
        HealthResource.objects.create(
            title=request.POST.get("title"),
            category_id=request.POST.get("category"),
            resource_type=request.POST.get("resource_type"),
            content=request.POST.get("content", ""),
            created_by=request.user,
            is_active=True,
        )

        messages.success(request, "Health resource added successfully.")
        return redirect("admin_panel:health_resource_list")

    return render(
        request,
        "admin_panel/health_resource_form.html",
        {"categories": categories}
    )


@login_required
@admin_required
def health_resource_edit(request, pk):
    """
    Edit health resource
    """
    resource = get_object_or_404(HealthResource, pk=pk)
    categories = HealthCategory.objects.filter(is_active=True)

    if request.method == "POST":
        resource.title = request.POST.get("title")
        resource.category_id = request.POST.get("category")
        resource.resource_type = request.POST.get("resource_type")
        resource.content = request.POST.get("content", "")
        resource.is_active = "is_active" in request.POST
        resource.save()

        messages.success(request, "Health resource updated successfully.")
        return redirect("admin_panel:health_resource_list")

    return render(
        request,
        "admin_panel/health_resource_edit.html",
        {
            "resource": resource,
            "categories": categories,
        }
    )


@login_required
@admin_required
def health_resource_delete(request, pk):
    """
    Delete health resource
    """
    resource = get_object_or_404(HealthResource, pk=pk)

    if request.method == "POST":
        resource.delete()
        messages.success(request, "Health resource deleted successfully.")
        return redirect("admin_panel:health_resource_list")

    return render(
        request,
        "admin_panel/health_resource_confirm_delete.html",
        {"resource": resource}
    )
def admin_panel_home(request):
    return redirect("admin_panel:dashboard")
