
from django.urls import path, include
from . import views
from rest_framework import routers
from .api_views import EventViewSet, TelegramUserViewSet, MeetingViewSet

router = routers.DefaultRouter()
router.register(r'api/events', EventViewSet)
router.register(r'api/users', TelegramUserViewSet)
router.register(r'api/meetings', MeetingViewSet)

urlpatterns = [
    path('export/', views.export_events, name='export_events'),
]

urlpatterns += router.urls
