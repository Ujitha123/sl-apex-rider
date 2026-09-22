from django.urls import path
from .views import BikeList, BikeCreate, BikeDetail
urlpatterns = [
    path('', BikeList.as_view(), name='bike-list'),
    path('add/', BikeCreate.as_view(), name='bike-add'),
    path('<int:pk>/', BikeDetail.as_view(), name='bike-detail'),
]
