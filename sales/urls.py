from django.urls import path
from .views import SaleList, sale_create, sale_bill, sale_send
urlpatterns = [
    path('', SaleList.as_view(), name='sale-list'),
    path('add/', sale_create, name='sale-add'),
    path('<int:sale_id>/bill/', sale_bill, name='sale-bill'),
    path('<int:sale_id>/send/', sale_send, name='sale-send'),
]
