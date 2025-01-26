from django.urls import path, include
from . import views


urlpatterns = [
    path('', views.home, name = 'home'),
    path('dashboard/', views.dashboard, name = 'dashboard'),
    path('analysis/', views.analysis, name='analysis'),
    path('futuregains/', views.futuregains, name='futuregains'),

]