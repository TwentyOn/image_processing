from rest_framework import serializers

"""
class Image(serializers.Serializer):
    format = serializers.CharField(max_length=10)
    quality = serializers.IntegerField()
    resolution = serializers.BooleanField()
    proportion = serializers.BooleanField()
    toggle_switch = serializers.BooleanField()
    high = serializers.IntegerField()
    width = serializers.IntegerField()
    file_format = serializers.CharField(max_length=10) # формат прикрепленного файла
                                                       # в потенциале нужно определять средствами python
"""


class InputImage(serializers.Serializer):
    format = serializers.CharField(max_length=25)
    quality = serializers.IntegerField()
    resolution = serializers.BooleanField()
    proportion = serializers.BooleanField()
    toggle_switch = serializers.BooleanField()
    high = serializers.IntegerField()
    width = serializers.IntegerField()
