from django.urls import path
from . import views

urlpatterns = [
    path('main/', views.page_timeevent),
    path('temp/', views.page_temperature),
    path('json/<str:ty>/', views.datajson),
    path('list/', views.page_listrecords),
    path('list/json/', views.recordasjson),
    path('query/', views.page_query),
    path('homepage/', views.home),
    path('<str:any>/', views.page_not_found),
    
]
