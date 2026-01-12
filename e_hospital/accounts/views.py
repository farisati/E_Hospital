from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required

from .forms import UserRegisterForm, ProfileUpdateForm

def register(request):
    if request.method == "POST":
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            user = form.save()
            role = form.cleaned_data.get("role")

            user.profile.role = role
            user.profile.save()

            messages.success(request, "Account created successfully!")
            return redirect("accounts:login")

    else:
        form = UserRegisterForm()

    return render(request, "accounts/register.html", {"form": form})


def login_view(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:

            if not user.is_active:
                messages.error(request, "Your account is inactive.")
                return redirect("accounts:login")

            login(request, user)

            profile = getattr(user, "profile", None)

            if not profile:
                messages.error(request, "User profile not found.")
                return redirect("accounts:login")

            if profile.role == "patient":
                return redirect("patient:dashboard")

            elif profile.role == "doctor":
                return redirect("doctor:dashboard")

            elif profile.role == "admin":
                return redirect("admin_panel:dashboard")

            else:
                messages.error(request, "Invalid user role.")
                return redirect("accounts:login")

        else:
            messages.error(request, "Invalid username or password")

    return render(request, "accounts/login.html")


def logout_view(request):
    logout(request)
    return redirect("home")


@login_required
def profile(request):
    if request.method == "POST":
        form = ProfileUpdateForm(request.POST, request.FILES, instance=request.user.profile)
        if form.is_valid():
            form.save()
            messages.success(request, "Profile Updated Successfully!")
            return redirect("accounts:profile")
    else:
        form = ProfileUpdateForm(instance=request.user.profile)

    return render(request, "accounts/profile.html", {"form": form})

def admin_login(request):
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(request, username=username, password=password)

        if user is not None:

            profile = getattr(user, "profile", None)

            if profile and profile.role == "admin":
                login(request, user)
                return redirect("admin_panel:dashboard")

            messages.error(request, "Admin access only")

        else:
            messages.error(request, "Invalid username or password")

    return render(request, "accounts/admin_login.html")
