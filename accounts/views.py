from accounts.models import CustomUser  # Ensure you're importing your CustomUser model
import re
from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth.models import User, auth
from .utils import send_otp
from django.contrib.auth import authenticate, login
import re
from django.contrib.auth import authenticate, login as auth_login
# from .models import CustomUser  # Import your custom user model
# Importing the get_user_model function to fetch the custom user model
from django.contrib.auth import get_user_model
# Assigning the custom or default User model to the variable User
User = get_user_model()

# Create your views here.


from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib import messages
import re


def login(request):
    if request.method == "POST":
        identifier = request.POST['identifier']
        password = request.POST['password']

        # Check if the identifier is an email
        if re.match(r"[^@]+@[^@]+\.[^@]+", identifier):
            # Use the correct user model
            user = authenticate(
                request, username=identifier, password=password)
        else:
            user = authenticate(
                request, username=identifier, password=password)

        if user is not None:
            auth_login(request, user)  # Log the user in
            # Redirect to the 'next' URL if available, otherwise to the dashboard
            next_url = request.GET.get('next', '/prediction/dashboard')
            return redirect(next_url)
        else:
            messages.info(request, 'Invalid credentials')
            # Ensure 'login' is the name of your login page URL
            return redirect('login')
    else:
        return render(request, 'login.html')




def register(request):
    if request.method == 'POST':
        fullname = request.POST['name']
        username = request.POST['username']
        password1 = request.POST['password']
        password2 = request.POST['confirm-password']
        email = request.POST['email']

        if password1 == password2:
            # To checkuser is already exist or not
            # User.objects refers to the Django User model's default manager,
            #                           which is used to query the database for all user-related objects.(Here we used custom user model)
            if User.objects.filter(username=username).exists():
                messages.info(request, 'Username Taken')
                return redirect('register')
            elif User.objects.filter(email=email).exists():
                messages.info(request, 'Email Taken')
                return redirect('register')
            else:
                otp = send_otp(email)
                request.session['otp'] = otp
                request.session['email'] = email
                request.session['fullname'] = fullname
                request.session['username'] = username
                request.session['password'] = password1
                messages.success(request, "OTP sent to your email.")
                return redirect('validate_otp')

    return render(request, 'register.html')


def validate_otp(request):
    if request.method == 'POST':
        # Concatenating the OTP digits
        otp = ''.join([
            request.POST.get(f'otp{i}', '') for i in range(1, 7)
        ])
        user_otp = otp
        if int(user_otp) == request.session.get('otp'):
            email = request.session.get('email')
            fullname = request.session.get('fullname')
            username = request.session.get('username')
            password = request.session.get('password')

            user = User.objects.create_user(
                username=username, password=password, email=email)
            user.fullname = fullname
            user.save()

            del request.session['otp']
            del request.session['email']
            del request.session['fullname']
            del request.session['username']
            del request.session['password']

            messages.success(request, "Registration successful.")
            return redirect('login')
        else:
            messages.error(request, "Invalid OTP.")
            return redirect('validate_otp')

    return render(request, 'validate_otp.html')


def resend_otp(request):
    email = request.session.get('email')
    if email:
        otp = send_otp(email)
        request.session['otp'] = otp
        messages.success(request, "A new OTP has been sent to your email.")
    else:
        messages.error(request, "Unable to resend OTP. Please try again.")
    return redirect('validate_otp')


def logout(request):
    auth.logout(request)
    return redirect('/')

