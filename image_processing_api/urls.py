from django.urls import path
from .views import ImageProcessing, index

urlpatterns = [
    path('', index),
    path('image_processing/', ImageProcessing.as_view())
]