from rest_framework import serializers
from django.contrib.postgres.fields import ArrayField


class ProviderParameters(serializers.Serializer):
    okpd2 = serializers.ListField(child=serializers.CharField(max_length=100), default=list)
    metrics = serializers.ListField(child=serializers.IntegerField(), default=list)
    regions = serializers.ListField(child=serializers.CharField(max_length=50), default=list)
    segment = serializers.CharField(required=False, max_length=50)
