from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='bot-home'),
    path('about/', views.about, name='bot-about'),
    path('dashboard/', views.dashboard, name='bot-dashboard'),
]