
import random
from django.core.mail import send_mail


def generate_otp():
    return random.randint(100000, 999999)  # 6-digit OTP


def send_otp(email):
    otp = generate_otp()
    subject = "Your OTP for Registration"
    message = f"Your OTP is {otp}. Please use this to complete your registration."
    from_email = 'your_email@gmail.com'
    send_mail(subject, message, from_email, [email])
    return otp
