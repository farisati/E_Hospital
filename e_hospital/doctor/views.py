# ======================================================
# DJANGO & PYTHON IMPORTS
# ======================================================
from functools import wraps

from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.core.paginator import Paginator
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login

# ======================================================
# APP IMPORTS
# ======================================================
from .models import DoctorProfile, Availability
from .forms import (
    AvailabilityForm,
    DoctorProfileForm,
    PrescriptionForm,
    MedicalRecordForm,
)

from patient.models import Appointment, Prescription, MedicalRecord
from accounts.models import Profile


# ======================================================
# AUTH / PERMISSION DECORATOR
# ======================================================

def doctor_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:
            profile = getattr(user, "profile", None)

            if profile and profile.role == "doctor":
                login(request, user)
                return redirect("doctor:dashboard")
            else:
                messages.error(request, "Only doctor access allowed.")

        else:
            messages.error(request, "Invalid username or password")

    return render(request, "doctor/login.html")

def doctor_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect("accounts:login")

        profile = getattr(request.user, "profile", None)

        if not profile or profile.role != "doctor":
            messages.error(request, "Access denied.")
            return redirect("accounts:login")

        return view_func(request, *args, **kwargs)

    return wrapper


# ======================================================
# DASHBOARD
# ======================================================
@login_required
@doctor_required
def dashboard(request):
    today = timezone.now().date()

    appointments = Appointment.objects.filter(
        doctor=request.user,
        date=today
    ).order_by("time")

    context = {
        "appointments": appointments,
        "today_count": appointments.count(),
        "pending_count": appointments.filter(status="pending").count(),
        "completed_count": appointments.filter(status="completed").count(),
        "cancelled_count": appointments.filter(status="cancelled").count(),
    }

    return render(request, "doctor/dashboard.html", context)


# ======================================================
# APPOINTMENTS
# ======================================================
@login_required
@doctor_required
def appointment_list(request):
    today = timezone.now().date()

    today_appointments = Appointment.objects.filter(
        doctor=request.user,
        date=today,
        status="confirmed"
    ).order_by("time")

    upcoming_appointments = Appointment.objects.filter(
        doctor=request.user,
        date__gt=today,
        status="confirmed"
    ).order_by("date", "time")

    completed_qs = Appointment.objects.filter(
        doctor=request.user,
        status="completed"
    ).order_by("-date", "-time")

    paginator = Paginator(completed_qs, 10)
    page_number = request.GET.get("page")
    completed_appointments = paginator.get_page(page_number)

    return render(request, "doctor/appointment_list.html", {
        "today_appointments": today_appointments,
        "upcoming_appointments": upcoming_appointments,
        "completed_appointments": completed_appointments,
    })


@login_required
@doctor_required
def appointment_detail(request, pk):
    appt = get_object_or_404(
        Appointment,
        pk=pk,
        doctor=request.user
    )

    has_record = MedicalRecord.objects.filter(
        appointment=appt
    ).exists()

    return render(request, "doctor/appointment_detail.html", {
        "appt": appt,
        "has_record": has_record
    })


@login_required
@doctor_required
def start_consultation(request, appointment_id):
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        doctor=request.user,
        status="confirmed"
    )

    record, created = MedicalRecord.objects.get_or_create(
        appointment=appointment,
        defaults={
            "patient": appointment.patient,
            "doctor": request.user,
        }
    )

    if created:
        messages.success(request, "Consultation started.")
    else:
        messages.info(request, "Consultation already started.")

    return redirect("doctor:appointment_detail", appointment.id)


@login_required
@doctor_required
def complete_appointment(request, appointment_id):
    appt = get_object_or_404(
        Appointment,
        id=appointment_id,
        doctor=request.user,
        status="confirmed"
    )

    if not MedicalRecord.objects.filter(appointment=appt).exists():
        messages.error(
            request,
            "Start consultation before completing the appointment."
        )
        return redirect("doctor:appointment_detail", appt.id)

    appt.status = "completed"
    appt.save()

    messages.success(request, "Appointment marked as completed.")
    return redirect("doctor:appointment_detail", appt.id)


# ======================================================
# AVAILABILITY
# ======================================================
@login_required
@doctor_required
def manage_availability(request):
    availabilities = Availability.objects.filter(
        doctor=request.user
    ).order_by("day_of_week", "start_time")

    return render(request, "doctor/availability_list.html", {
        "availabilities": availabilities
    })


@login_required
@doctor_required
def add_availability(request):
    form = AvailabilityForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        availability = form.save(commit=False)
        availability.doctor = request.user
        availability.save()
        messages.success(request, "Availability added.")
        return redirect("doctor:manage_availability")

    return render(request, "doctor/availability_form.html", {"form": form})


@login_required
@doctor_required
def edit_availability(request, pk):
    availability = get_object_or_404(
        Availability,
        pk=pk,
        doctor=request.user
    )

    form = AvailabilityForm(request.POST or None, instance=availability)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Availability updated.")
        return redirect("doctor:manage_availability")

    return render(request, "doctor/availability_form.html", {"form": form})


@login_required
@doctor_required
def delete_availability(request, pk):
    availability = get_object_or_404(
        Availability,
        pk=pk,
        doctor=request.user
    )

    if request.method == "POST":
        availability.delete()
        messages.success(request, "Availability deleted.")
        return redirect("doctor:manage_availability")

    return render(
        request,
        "doctor/availability_confirm_delete.html",
        {"availability": availability}
    )


# ======================================================
# MEDICAL RECORDS
# ======================================================
@login_required
@doctor_required
def add_record(request, appointment_id):
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        doctor=request.user
    )

    if request.method == "POST":
        record = MedicalRecord.objects.create(
            patient=appointment.patient,
            doctor=request.user,
            appointment=appointment,
            diagnosis=request.POST.get("diagnosis"),
            notes=request.POST.get("notes"),
        )

        meds = request.POST.getlist("medication")
        insts = request.POST.getlist("instructions")

        for med, ins in zip(meds, insts):
            Prescription.objects.create(
                record=record,
                medication=med,
                instructions=ins
            )

        return redirect("doctor:appointment_detail", appointment_id)

    return render(request, "doctor/add_record.html")


@login_required
@doctor_required
def edit_medical_record(request, appointment_id):
    appointment = get_object_or_404(Appointment,id=appointment_id,doctor=request.user)

    record = get_object_or_404(MedicalRecord,appointment=appointment)

    form = MedicalRecordForm(request.POST or None, instance=record)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Medical record updated.")
        return redirect("doctor:appointment_detail", appointment.id)

    return render(request, "doctor/edit_medical_record.html", {
        "form": form,
        "appt": appointment
    })


@login_required
@doctor_required
def patient_medical_history(request, pk):
    appointment = get_object_or_404(
        Appointment,
        pk=pk,
        doctor=request.user
    )

    records = MedicalRecord.objects.filter(
        patient=appointment.patient
    ).order_by("-created_at")

    return render(request, "doctor/patient_medical_history.html", {
        "appointment": appointment,
        "patient": appointment.patient,
        "records": records
    })


# ======================================================
# PRESCRIPTIONS
# ======================================================
@login_required
@doctor_required
def view_prescription(request, appointment_id):
    prescription = Prescription.objects.filter(
        record__appointment_id=appointment_id
    ).first()

    return render(request, "doctor/view_prescription.html", {
        "prescription": prescription,
        "appointment_id": appointment_id
    })


@login_required
@doctor_required
def create_prescription(request, appointment_id):
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        doctor=request.user
    )

    record, _ = MedicalRecord.objects.get_or_create(
        appointment=appointment,
        defaults={
            "patient": appointment.patient,
            "doctor": request.user,
        }
    )

    if Prescription.objects.filter(record=record).exists():
        messages.warning(request, "Prescription already exists.")
        return redirect("doctor:view_prescription", appointment_id)

    form = PrescriptionForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        prescription = form.save(commit=False)
        prescription.record = record
        prescription.save()
        messages.success(request, "Prescription created.")
        return redirect("doctor:view_prescription", appointment_id)

    return render(request, "doctor/create_prescription.html", {
        "form": form,
        "appointment": appointment
    })


# ======================================================
# PATIENTS
# ======================================================
@login_required
@doctor_required
def patient_list(request):
    patients = Profile.objects.filter(role="patient")
    return render(request, "doctor/patient_list.html", {
        "patients": patients
    })


# ======================================================
# DOCTOR PROFILE
# ======================================================
@login_required
@doctor_required
def profile(request):
    doctor, _ = DoctorProfile.objects.get_or_create(user=request.user)
    return render(request, "doctor/profile.html", {"doctor": doctor})


@login_required
@doctor_required
def profile_edit(request):
    doctor, _ = DoctorProfile.objects.get_or_create(user=request.user)

    form = DoctorProfileForm(
        request.POST or None,
        request.FILES or None,
        instance=doctor
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Profile updated successfully.")
        return redirect("doctor:profile")

    return render(request, "doctor/profile_edit.html", {"form": form})
