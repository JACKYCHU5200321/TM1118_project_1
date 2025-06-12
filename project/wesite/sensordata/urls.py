from django.urls import path
from . import views

urlpatterns = [
    path('stat/<str:ty>/', views.page_statchart),
    path('json/latest/', views.json_latestsummary),
    path('json/<str:ty>/', views.json_data),
    path('list/', views.page_listrecords),
    path('list/json/', views.json_records),
    path('query/', views.page_query),
    path('node/', views.page_node),
    path('homepage/', views.home),
    path('memberlist/', views.member),
    path('<str:any>/', views.page_not_found),
]
