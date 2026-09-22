from django.urls import path
from .views import PartList, PartCreate
urlpatterns = [
    path('', PartList.as_view(), name='part-list'),
    path('add/', PartCreate.as_view(), name='part-add'),
]
