from django.urls import path
from . import views

app_name = "admin_panel"

urlpatterns = [
    path("", views.admin_panel_home, name="admin_panel_home"),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('doctors/', views.doctor_list, name='doctor_list'),
    path('patients/', views.patient_list, name='patient_list'),
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/<int:pk>/approve/', views.approve_appointment, name='approve_appointment'),
   
    path('payments/', views.payments, name='payments'),

    path('billing/', views.billing_list, name='billing_list'),
    path('billing/add/', views.billing_create, name='billing_create'),
    path('billing/<int:pk>/edit/', views.billing_edit, name='billing_edit'),
    path('billing/<int:pk>/delete/', views.billing_delete, name='billing_delete'),

    # Add payment for a bill (admin)
    path('billing/<int:billing_pk>/payment/add/', views.payment_create, name='payment_create_for_bill'),
    path('payment/add/', views.payment_create, name='payment_create'),

   

path("insurance/", views.insurance_list, name="insurance_list"),
path("insurance/add/", views.insurance_add, name="insurance_add"),
path("insurance/<int:id>/edit/", views.insurance_edit, name="insurance_edit"),
path("insurance/<int:id>/delete/", views.insurance_delete, name="insurance_delete"),

path("get-insurance/<int:patient_id>/", views.get_insurance, name="get_insurance"),


# Doctor Management
path("doctors/add/", views.doctor_add, name="doctor_add"),
path("doctors/<int:doctor_id>/edit/", views.doctor_edit, name="doctor_edit"),
path("doctors/<int:doctor_id>/delete/", views.doctor_delete, name="doctor_delete"),

# Patient Management
path("patients/add/", views.patient_add, name="patient_add"),
path("patients/<int:patient_id>/edit/", views.patient_edit, name="patient_edit"),
path("patients/<int:patient_id>/deactivate/", views.patient_deactivate, name="patient_deactivate"),
path("patients/<int:patient_id>/view/", views.patient_view, name="patient_view"),
path("patients/<int:user_id>/activate/", views.patient_activate, name="patient_activate"),

path("appointments/<int:pk>/", views.appointment_detail,name="appointment_detail"),

path("health-categories/",views.health_category_list,name="admin_health_categories"),
path("health-resources/",views.health_resource_list,name="health_resource_list"),
path("health-resources/add/",views.health_resource_add,name="admin_health_resource_add"),
path("health-categories/add/",views.health_category_add,name="admin_health_category_add"),
path("health-resources/<int:pk>/edit/",views.health_resource_edit,name="admin_health_resource_edit"),
path("health-resources/<int:pk>/delete/",views.health_resource_delete,name="admin_health_resource_delete"),
path(
    "health-categories/<int:pk>/toggle/",
    views.health_category_toggle,
    name="admin_health_category_toggle"
),  


]
