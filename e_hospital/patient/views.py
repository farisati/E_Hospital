from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.utils import timezone
from django.http import JsonResponse
from functools import wraps
import datetime
import stripe
from .forms import ProfileForm
from django.conf import settings
from doctor.models import Availability
from .forms import AppointmentForm
from .models import (
    Appointment, MedicalRecord, Prescription,
    Payment, Billing, Insurance, HealthCategory, HealthResource
)

from django.contrib.auth import authenticate, login



# =====================================================
# PATIENT ROLE CHECK DECORATOR
# =====================================================

def patient_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:

            profile = getattr(user, "profile", None)

            # 🔒 Allow ONLY patients
            if profile and profile.role == "patient":
                login(request, user)
                return redirect("patient:dashboard")

            else:
                messages.error(request, "Only patient access allowed.")
                return redirect("patient:login")

        else:
            messages.error(request, "Invalid username or password")

    return render(request, "patient/login.html")


def patient_required(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if not request.user.is_authenticated:
                return redirect("accounts:login")

            profile = getattr(request.user, "profile", None)

            if not profile or profile.role != "patient":
                messages.error(request, "Access denied.")
                return redirect("accounts:login")

            return view_func(request, *args, **kwargs)
        return wrapper


# =====================================================
# DASHBOARD
# =====================================================
@login_required
@patient_required
def dashboard(request):
    user = request.user

    upcoming = Appointment.objects.filter(patient=user,date__gte=timezone.now().date()).order_by("date", "time")[:5]
    recent_records = MedicalRecord.objects.filter(patient=user).order_by("-created_at")[:3]
    recent_payments = Payment.objects.filter(patient=user).order_by("-paid_at")[:5]

    return render(request, "patient/dashboard.html", {
        "upcoming": upcoming,
        "recent_records": recent_records,
        "payments": recent_payments,
    })


# =====================================================
# APPOINTMENTS
# =====================================================
@login_required
@patient_required
def appointment_list(request):
    user = request.user
    return render(request, "patient/appointment_list.html", {
        "pending": Appointment.objects.filter(patient=user, status="pending"),
        "approved": Appointment.objects.filter(patient=user, status="confirmed"),
        "cancelled": Appointment.objects.filter(patient=user, status="cancelled"),
        "completed": Appointment.objects.filter(patient=request.user,status='completed').order_by('-date', '-time')
    })


@login_required
@patient_required
def appointment_detail(request, pk):
    appt = get_object_or_404(Appointment, pk=pk, patient=request.user)
    return render(request, "patient/appointment_detail.html", {"appointment": appt})


@login_required
@patient_required
def book_appointment(request):
    if request.method == "POST":
        form = AppointmentForm(request.POST)

        date_str = request.POST.get("date")
        time_str = request.POST.get("time")

        # 🔴 HARD VALIDATION
        if not date_str or not time_str:
            messages.error(request, "Please select doctor, date and time slot")
            return redirect("patient:book_appointment")

        if not form.is_valid():
            print("FORM ERRORS:", form.errors)  # 🔍 DEBUG
            messages.error(request, "Invalid form data")
            return redirect("patient:book_appointment")

        # ✅ CONVERT STRING → DATE & TIME
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
        time_obj = datetime.datetime.strptime(time_str, "%I:%M %p").time()

        appt = form.save(commit=False)
        appt.patient = request.user
        appt.date = date_obj
        appt.time = time_obj
        appt.status = "pending"
        appt.save()

        messages.success(request, "Appointment booked successfully")
        return redirect("patient:appointment_list")

    else:
        form = AppointmentForm()

    return render(request, "patient/book_appointment.html", {
        "form": form
    })


@login_required
@patient_required
def reschedule_appointment(request, pk):
    appt = get_object_or_404(
        Appointment,
        pk=pk,
        patient=request.user
    )

    # Only pending or confirmed can be rescheduled
    if appt.status not in ["pending", "confirmed"]:
        messages.error(request, "Cannot reschedule this appointment.")
        return redirect("patient:appointment_list")

    if request.method == "POST":
        form = AppointmentForm(request.POST, instance=appt)
        if form.is_valid():
            appt = form.save(commit=False)
             # 🔥 FIX 1: DATE
            date_str = request.POST.get("date")
            if date_str:
                appt.date = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()

            # 🔥 FIX 2: TIME
            time_str = request.POST.get("time")
            if time_str:
                appt.time = datetime.datetime.strptime(time_str, "%I:%M %p").time()

                

            # 🔁 Reset approval
            appt.status = "pending"
            appt.save()
            messages.success(
                request,
                "Appointment rescheduled. Waiting for admin approval."
            )
            return redirect("patient:appointment_list")
    else:
        form = AppointmentForm(instance=appt)

    return render(request, "patient/reschedule_appointment.html", {
        "form": form,
        "reschedule": True,
        "appt": appt,
    })


@login_required
@patient_required
def cancel_appointment(request, pk):
    appt = get_object_or_404(Appointment, pk=pk, patient=request.user)

    if appt.status in ["pending", "confirmed"]:
        appt.status = "cancelled"
        appt.save()
        messages.success(request, "Appointment cancelled.")
    else:
        messages.error(request, "Cannot cancel this appointment.")

    return redirect("patient:appointment_list")


# =====================================================
# MEDICAL HISTORY
# =====================================================
@login_required
@patient_required
def medical_history(request):
    records = MedicalRecord.objects.filter(
        patient=request.user
    ).order_by("-created_at")

    paginator = Paginator(records, 10)
    page = request.GET.get("page")
    records = paginator.get_page(page)

    return render(request, "patient/medical_history.html", {"records": records})


@login_required
@patient_required
def record_detail(request, record_id):
    record = get_object_or_404(MedicalRecord, id=record_id, patient=request.user)
    return render(request, "patient/record_detail.html", {"record": record})


# =====================================================
# PRESCRIPTIONS
# =====================================================
@login_required
@patient_required
def prescription_detail(request, pk):
    pres = get_object_or_404(Prescription, pk=pk, record__patient=request.user)
    return render(request, "patient/prescription_detail.html", {"prescription": pres})


@login_required
@patient_required
def my_prescriptions(request):
    prescriptions = Prescription.objects.filter(record__patient=request.user)
    return render(request, "patient/my_prescriptions.html", {"prescriptions": prescriptions})





# =====================================================
# AVAILABLE SLOTS (AJAX)
# =====================================================
@login_required
@patient_required
def get_available_slots(request):
    doctor_id = request.GET.get("doctor")
    date_str = request.GET.get("date")

    if not doctor_id or not date_str:
        return JsonResponse({"slots": []})

    try:
        date_obj = datetime.datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        return JsonResponse({"slots": []})

    day_of_week = date_obj.weekday()
    availability = Availability.objects.filter(
        doctor_id=doctor_id,
        day_of_week=day_of_week
    ).first()

    if not availability:
        return JsonResponse({"slots": []})

    slots = []
    current_time = datetime.datetime.combine(date_obj, availability.start_time)
    end_time = datetime.datetime.combine(date_obj, availability.end_time)
    duration = datetime.timedelta(minutes=availability.slot_duration_minutes)

    while current_time + duration <= end_time:
        slots.append(current_time.time())
        current_time += duration

    booked_times = Appointment.objects.filter(
        doctor_id=doctor_id,
        date=date_obj,
        status__in=["pending", "confirmed"]
    ).values_list("time", flat=True)

    now = datetime.datetime.now().time()
    final_slots = []

    for t in slots:

        # ⛔ Skip today's past slots
        if date_obj == datetime.date.today() and t <= now:
            continue

        # ⛔ Skip lunch break (1 PM – 2 PM)
        if datetime.time(13, 0) <= t < datetime.time(14, 0):
            continue

        # ⛔ Skip booked slots
        if t in booked_times:
            continue

        # ✅ Add valid slot
        final_slots.append(t.strftime("%I:%M %p"))

    return JsonResponse({"slots": final_slots})



# =====================================================
# BILLING + PAYMENTS
# =====================================================
@login_required
def billing_list(request):
    bills = Billing.objects.filter(patient=request.user).order_by('-created_at')
    return render(request, "patient/billing_list.html", {"bills": bills})


@login_required
@patient_required
def billing_detail(request, pk):
    bill = get_object_or_404(Billing, pk=pk, patient=request.user)

    # Payments made for this bill (even though only one full payment exists)
    payments = bill.payments.order_by('-paid_at')

    return render(request, "patient/billing_detail.html", {
        "bill": bill,
        "payments": payments,
        "can_pay": bill.status == "unpaid",   # 👈 New: Show pay button only if unpaid
    })

@login_required
@patient_required
def pay_bill(request, pk):
    bill = get_object_or_404(Billing, pk=pk, patient=request.user)

    stripe.api_key = settings.STRIPE_SECRET_KEY

    # Stripe requires integer paise value
    amount_in_paise = int(bill.amount_due * 100)

    checkout_session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[
            {
                "price_data": {
                    "currency": "inr",
                    "unit_amount": amount_in_paise,   # 👈 FULL amount_due
                    "product_data": {
                        "name": bill.description,
                    },
                },
                "quantity": 1,
            }
        ],
        mode="payment",
        success_url=f"{settings.STRIPE_SUCCESS_URL}?bill_id={bill.id}",
        cancel_url=settings.STRIPE_CANCEL_URL,
    )

    return redirect(checkout_session.url)


@login_required
@patient_required
def payment_success(request):
    bill_id = request.GET.get("bill_id")
    bill = get_object_or_404(Billing, pk=bill_id, patient=request.user)

    # -----------------------------
    # AVOID MULTIPLE PAYMENTS
    # -----------------------------
    if bill.status == "paid":
        messages.info(request, "This bill is already paid.")
        return redirect("patient:billing_list")

    # -----------------------------
    # CREATE PAYMENT RECORD
    # -----------------------------
    Payment.objects.create(
        billing=bill,
        patient=request.user,
        amount=bill.amount_due,      # full amount paid
        method="card",
        status="paid",
        transaction_id="Stripe-Auto",
    )

    # -----------------------------
    # UPDATE BILL
    # -----------------------------
    bill.status = "paid"
    bill.amount_due = 0
    bill.save()

    messages.success(request, "Payment successful!")
    return redirect("patient:billing_list")



@login_required
@patient_required
def payment_cancel(request):
    messages.error(request, "Payment canceled.")
    return redirect("patient:billing_list")


# =====================================================
# INSURANCE INFO
# =====================================================
@login_required
@patient_required
def insurance_info(request):
    insurance = Insurance.objects.filter(patient=request.user).first()
    return render(request, "patient/insurance.html", {"insurance": insurance})


@login_required
@patient_required
def invoice_view(request, pk):
    bill = get_object_or_404(Billing, pk=pk, patient=request.user)
    payments = bill.payments.order_by('-paid_at')

    return render(request, "patient/invoice.html", {
        "bill": bill,
        "payments": payments
    })


@login_required
@patient_required
def profile_page(request):
    profile = request.user.profile
    insurance = Insurance.objects.filter(patient=request.user).first()

    return render(request, "patient/profile.html", {
        "profile": profile,
        "insurance": insurance
    })

@login_required
@patient_required
def edit_profile(request):
    profile = request.user.profile

    if request.method == "POST":
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile updated successfully!")
            return redirect("patient:profile")
    else:
        form = ProfileForm(instance=profile)

    return render(request, "patient/edit_profile.html", {"form": form})


def get_available_dates(request):
    doctor_id = request.GET.get("doctor")
    if not doctor_id:
        return JsonResponse({"dates": []})

    working_days = set(
        Availability.objects.filter(doctor_id=doctor_id)
        .values_list("day_of_week", flat=True)
    )

    available_dates = []
    today = timezone.now().date()

    for i in range(14):
        future_date = today + datetime.timedelta(days=i)

        if future_date.weekday() not in working_days:
            continue

        day_availabilities = Availability.objects.filter(
            doctor_id=doctor_id,
            day_of_week=future_date.weekday()
        )

        day_has_slot = False
        now_time = timezone.now().time()

        for av in day_availabilities:
            current = datetime.datetime.combine(future_date, av.start_time)
            end = datetime.datetime.combine(future_date, av.end_time)
            duration = datetime.timedelta(minutes=av.slot_duration_minutes)

            while current + duration <= end:
                slot_time = current.time()

                if future_date == today and slot_time <= now_time:
                    current += duration
                    continue

                is_booked = Appointment.objects.filter(
                    doctor_id=doctor_id,
                    date=future_date,
                    time=slot_time,
                    status__in=["pending", "confirmed"]
                ).exists()

                if not is_booked:
                    day_has_slot = True
                    break

                current += duration

            if day_has_slot:
                break

        if day_has_slot:
            available_dates.append(future_date.strftime("%Y-%m-%d"))

    return JsonResponse({"dates": available_dates})

@login_required
@patient_required
def health_resources(request):
    categories = HealthCategory.objects.filter(is_active=True)
    resources = HealthResource.objects.filter(is_active=True)

    return render(
        request,
        "patient/health_resources.html",
        {
            "categories": categories,
            "resources": resources
        }
    )


@login_required
@patient_required
def health_resource_detail(request, pk):
    resource = get_object_or_404(HealthResource,pk=pk,is_active=True)

    return render(request,"patient/health_resource_detail.html",{"resource": resource})




