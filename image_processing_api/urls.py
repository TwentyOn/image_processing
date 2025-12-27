from django.urls import path
from .views import ImageProcessing

urlpatterns = [
    path('', ImageProcessing.as_view())
]
