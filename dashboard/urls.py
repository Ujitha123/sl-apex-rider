from django.urls import path
from .views import home, cover
urlpatterns = [path('', home, name='home'), path('welcome/', cover, name='cover')]
