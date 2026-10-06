
from django.urls import path
from . import views

urlpatterns = [
    path('export/', views.export_events, name='export_events'),
]
