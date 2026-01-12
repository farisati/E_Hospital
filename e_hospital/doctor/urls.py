from django.urls import path
from . import views

app_name = 'doctor'

urlpatterns = [
    path("login/", views.doctor_login, name="login"),
    path('', views.dashboard, name='dashboard'),
    path('appointments/', views.appointment_list, name='appointment_list'),
    path('appointments/<int:pk>/', views.appointment_detail, name='appointment_detail'),
    path('appointments/<int:appointment_id>/add-record/', views.add_record, name='add_record'),
    path("prescription/<int:appointment_id>/",views.view_prescription,name="view_prescription" ),
    path("prescription/<int:appointment_id>/create/",views.create_prescription,name="create_prescription"),
    path("appointments/<int:appointment_id>/start/",views.start_consultation,name="start_consultation" ),
    path("appointments/<int:appointment_id>/complete/",views.complete_appointment,name="complete_appointment"),
    path("appointments/<int:appointment_id>/record/",views.edit_medical_record, name="edit_medical_record"),
    path("appointments/<int:pk>/history/",views.patient_medical_history,name="patient_medical_history"),

    path('availability/', views.manage_availability, name='manage_availability'),
    path('availability/add/', views.add_availability, name='add_availability'),
    path('availability/<int:pk>/edit/', views.edit_availability, name='edit_availability'),
    path('availability/<int:pk>/delete/', views.delete_availability, name='delete_availability'),

    path('patients/', views.patient_list, name='patient_list'),

    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    
]
