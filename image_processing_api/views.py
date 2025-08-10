import os.path

from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse, FileResponse
from django.conf.urls.static import static

from PIL import Image

import io, base64
from pathlib import Path

from .serializers import InputImage


def index(request):
    return render(request, 'index.html')


class ImageProcessing(APIView):
    def get(self, request):
        print(request.data)
        return Response(request.method)

    def post(self, request):
        serializer = InputImage(data=request.data)
        if serializer.is_valid():
            print(static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT))
            file = request.FILES['file']
            default_storage.save(file.name, ContentFile(file.read()))
            if file.name.endswith('.zip'):
                pass
            else:
                new_file_name = file.name.split('.')[0] + f'.{serializer.validated_data["format"]}'
                image = self.image_process(file, serializer.validated_data, new_file_name)
                # high, width = image.size
                # image = image.resize((high // 5, width // 5))
                output = io.BytesIO()
                image.save(output, format=serializer.validated_data['format'])
                output.seek(0)
                file_url = request.build_absolute_uri(os.path.join(settings.MEDIA_URL, f'download/{new_file_name}'))
                return Response({'file_url': file_url})
                # return FileResponse(output, filename=f'processed_{file.name}', content_type='image/WEBP')
        return Response({'status': 'error'})

    def image_process(self, image_file: Image, inp_settings: dict, new_file_name):
        image = Image.open(image_file)

        if inp_settings['resolution']:
            high, width = image.size
            image = image.resize((high, width))
        image.save(os.path.join(settings.MEDIA_ROOT, f'download\\{new_file_name}'), quality=inp_settings['quality'],
                   format=inp_settings['format'].upper())
        image = Image.open(os.path.join(settings.MEDIA_ROOT, f'download\\{new_file_name}'))
        return image

    def zip_processing(self, file):
        pass
