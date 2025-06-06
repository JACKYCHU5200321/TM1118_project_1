from django.urls import path
from . import views

urlpatterns = [
    path('venueevent/', views.index),
]