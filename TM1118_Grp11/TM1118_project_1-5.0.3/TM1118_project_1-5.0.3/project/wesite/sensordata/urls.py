from django.urls import path, re_path
from . import views

urlpatterns = [
    path('stat/<str:ty>/', views.page_statchart),
    path('json/latest/', views.json_latestsummary),
    path('json/<str:ty>/', views.json_data),
    path('list/', views.page_listrecords),
    path('list/json/', views.json_records),
    path('query/', views.page_query),
    path('event/', views.page_queryevent),
    path('node/', views.page_node),
    path('alert/', views.page_alert),
    path('homepage/', views.home),
    path('memberlist/', views.member),
    re_path(r'^.*$', views.page_not_found),
]
