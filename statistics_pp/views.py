from django.shortcuts import render
from rest_framework.response import Response
from rest_framework.views import APIView
from .serializers import ProviderParameters
import json


# Create your views here.
class ProviderStatistic(APIView):
    def post(self, request):
        print(request.data)
        parameters = ProviderParameters(data=request.data)
        if parameters.is_valid():
            return Response(parameters.data)
        else:
            print(parameters.errors)
            return Response({'status': 'Ошибка'})
