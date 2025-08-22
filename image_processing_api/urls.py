from django.urls import path
from .views import ImageProcessing, GetImage

urlpatterns = [
    path('image_processing/', ImageProcessing.as_view()),
    path('image_processing/download/<str:filename>/', GetImage.as_view()) # url на скачивание файлов
]
