from django.urls import path
from .views import ProviderStatistic

urlpatterns = [
    path('', ProviderStatistic().as_view())
]
