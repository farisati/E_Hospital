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

        user = authenticate(username=username, password=password)

        if user:
            login(request, user)

            if user.profile.role == "patient":
                return redirect("patient:dashboard")

            elif user.profile.role == "doctor":
                return redirect("doctor:dashboard")

            else:
                return redirect("admin_panel:dashboard")

        else:
            messages.error(request, "Invalid username or password")

    return render(request, "accounts/login.html")


def logout_view(request):
    logout(request)
    return redirect("accounts:login")


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

