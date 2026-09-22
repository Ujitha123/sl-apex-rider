from django.urls import path
from .views import ServiceList, ServiceCreate, AlertList
urlpatterns = [
    path('', ServiceList.as_view(), name='service-list'),
    path('add/', ServiceCreate.as_view(), name='service-add'),
    path('alerts/', AlertList.as_view(), name='alert-list'),
]
