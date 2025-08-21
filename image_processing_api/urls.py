from django.urls import path
from .views import ImageProcessing

urlpatterns = [
    path('image_processing/', ImageProcessing.as_view())
]
