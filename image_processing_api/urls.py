from django.urls import path
from .views import ImageProcessing, GetImage

urlpatterns = [
    path('', ImageProcessing.as_view()),
    path('download/<str:filename>/', GetImage.as_view()) # url на скачивание файлов
]
