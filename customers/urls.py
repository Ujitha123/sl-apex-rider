from django.urls import path
from .views import CustomerList, CustomerCreate, CustomerUpdate
urlpatterns = [
    path('', CustomerList.as_view(), name='customer-list'),
    path('add/', CustomerCreate.as_view(), name='customer-add'),
    path('<int:pk>/edit/', CustomerUpdate.as_view(), name='customer-edit'),
]
