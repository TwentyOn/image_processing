import os.path
from zipfile import ZipFile

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
            file = request.FILES['file']
            default_storage.save(file.name, ContentFile(file.read()))
            if file.name.lower().endswith('.zip'):
                self.zip_processing(request.FILES['file'])
            elif file.name.lower().endswith(('.png', '.webp', '.jpg', '.jpeg')):
                new_file_name = file.name.split('.')[0] + f'.{serializer.validated_data["format"]}'
                self.image_process(file, serializer.validated_data,
                                   new_file_name)  # вызов функции обработки изображения
                file_url = request.build_absolute_uri(os.path.join(settings.MEDIA_URL, f'download/{new_file_name}'))
                return Response({'file_url': file_url})
                # return FileResponse(output, filename=f'processed_{file.name}', content_type='image/WEBP')
        return Response({'status': 'error'})

    def image_process(self, image_file: Image, inp_settings: dict, new_file_name):
        image = Image.open(image_file)

        if not inp_settings['resolution']:  # если False то меняем разрешение
            if inp_settings['proportion']:  # если True сохраняем пропорции
                width, high = image.size
                aspect_ratio = width / high  # считаем соотношение сторон
                if not inp_settings['toggle_switch']:  # если False редактируется высота
                    image = image.resize((int(inp_settings['high'] / aspect_ratio), inp_settings['high']))
                else:  # если True редактируется ширина
                    image = image.resize((inp_settings['width'], int(inp_settings['width'] * aspect_ratio)))
            else:
                image = image.resize((inp_settings['width'], inp_settings['high']))
        image.save(os.path.join(settings.MEDIA_ROOT, f'download\\{new_file_name}'), quality=inp_settings['quality'],
                   format=inp_settings['format'].upper())  # сохраняём в качестве quality и формате format
        image.close()
        #image = Image.open(os.path.join(settings.MEDIA_ROOT, f'download\\{new_file_name}'))

    def zip_processing(self, file):
        image_files = []
        with ZipFile(file) as zip_file:
            for file in zip_file.infolist():
                if file.filename.lower().endswith(('.png', '.webp', '.jpg', '.jpeg')):
                    image_files.append(file.filename)
        print(image_files)