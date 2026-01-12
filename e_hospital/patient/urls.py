from django.urls import path
from . import views

app_name = "patient"

urlpatterns = [
    path('login/', views.patient_login, name='login'),

    # ✅ Dashboard
    path("", views.dashboard, name="dashboard"),

    # ✅ Appointments
    path("appointments/", views.appointment_list, name="appointment_list"),
    path("appointments/book/", views.book_appointment, name="book_appointment"),
    path("appointments/<int:pk>/", views.appointment_detail, name="appointment_detail"),
    path("appointments/<int:pk>/reschedule/", views.reschedule_appointment, name="reschedule_appointment"),
    path("appointments/<int:pk>/cancel/", views.cancel_appointment, name="cancel_appointment"),

    # ✅ Medical Records
    path("medical-history/", views.medical_history, name="medical_history"),
    path("medical-history/record/<int:record_id>/", views.record_detail, name="record_detail"),

    # ✅ Prescriptions
    path("prescriptions/", views.my_prescriptions, name="my_prescriptions"),
    path("prescriptions/<int:pk>/", views.prescription_detail, name="prescription_detail"),

    
    # ✅ Slot Availability (AJAX endpoint)
    path("appointments/slots/", views.get_available_slots, name="get_available_slots"),

    # ✅ Profile Page
    path("profile/", views.profile_page, name="profile"),
    path("profile/edit/", views.edit_profile, name="edit_profile"), 

    # ✅ Billing Dashboard + Detail
    path("billing/", views.billing_list, name="billing_list"),
    path("billing/<int:pk>/", views.billing_detail, name="billing_detail"),

    # ✅ Stripe Payment Handling
    path("billing/<int:pk>/pay/", views.pay_bill, name="pay_bill"),
    path("payment/success/", views.payment_success, name="payment_success"),
    path("payment/cancel/", views.payment_cancel, name="payment_cancel"),

    path("insurance/", views.insurance_info, name="insurance_info"),
    path("invoice/<int:pk>/", views.invoice_view, name="invoice_view"),

    
    path("get-available-dates/", views.get_available_dates, name="get_available_dates"),
    path("get-available-slots/", views.get_available_slots, name="get_available_slots"),


    path("health-resources/",views.health_resources,name="health_resources"),
    path("health-resources/<int:pk>/",views.health_resource_detail,name="health_resource_detail"),
    
]
