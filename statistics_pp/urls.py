from django.urls import path
from .views import ProviderStatistic, GetMetricsRegions, GetOkpd2Segments, CreateSegment, GetChieldForOkpd2

urlpatterns = [
    path('', ProviderStatistic().as_view()),
    path('data/metrics_regions/', GetMetricsRegions().as_view()),
    path('data/okpd2_segments/', GetOkpd2Segments.as_view()),
    path('data/okpd2_chields/', GetChieldForOkpd2.as_view()),
    path('create/segment/', CreateSegment.as_view())
]
