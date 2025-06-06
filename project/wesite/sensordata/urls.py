from django.urls import path
from . import views

urlpatterns = [
    path('sensordata/index/', views.index),
    path('sensordata/index2/', views.index2),
    path('main/', views.page_timeevent),
]