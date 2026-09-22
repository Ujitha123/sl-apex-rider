from django.urls import path
from .views import SaleList, sale_create
urlpatterns = [
    path('', SaleList.as_view(), name='sale-list'),
    path('add/', sale_create, name='sale-add'),
]
