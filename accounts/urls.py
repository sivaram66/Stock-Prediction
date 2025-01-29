from django.urls import path, include
from . import views


urlpatterns = [
    path('login/', views.login, name='login'),
    path('register/', views.register, name='register'),
    path('validate-otp/', views.validate_otp, name='validate_otp'),
    path('validate-otp2/', views.validate_otp2, name='validate_otp2'),
    path('resend-otp/', views.resend_otp, name='resend_otp'),
    path('logout/', views.logout, name='logout'),
    path('forget_password/', views.forget_password, name='forget_password'),
    path('reset_password/', views.reset_password, name='reset_password'),


]
