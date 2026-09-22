from django.urls import path
from .views import (
    SaleList, sale_create, sale_bill, sale_send,
    EstimateList, estimate_create, estimate_detail, estimate_send,
    estimate_convert, estimate_complete,
)
urlpatterns = [
    path('', SaleList.as_view(), name='sale-list'),
    path('add/', sale_create, name='sale-add'),
    path('<int:sale_id>/bill/', sale_bill, name='sale-bill'),
    path('<int:sale_id>/send/', sale_send, name='sale-send'),
    path('estimates/', EstimateList.as_view(), name='estimate-list'),
    path('estimates/add/', estimate_create, name='estimate-add'),
    path('estimates/<int:est_id>/', estimate_detail, name='estimate-detail'),
    path('estimates/<int:est_id>/send/', estimate_send, name='estimate-send'),
    path('estimates/<int:est_id>/convert/', estimate_convert, name='estimate-convert'),
    path('estimates/<int:est_id>/complete/', estimate_complete, name='estimate-complete'),
]
