import os.path

from django.shortcuts import render

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.http import HttpResponse, FileResponse

from PIL import Image

import io, base64
from pathlib import Path

from .serializers import InputImage

OUTPUT_WORK_DIR = Path(__file__).resolve().parent / 'static' / 'image' / 'upload'


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
            if file.name.endswith('.zip'):
                pass
            else:
                image = self.image_process(file, serializer.validated_data)
                print(image.format)
                # high, width = image.size
                # image = image.resize((high // 5, width // 5))
                output = io.BytesIO()
                image.save(output, format=serializer.validated_data['format'])
                output.seek(0)
                #return HttpResponse(output.getvalue(), content_type='image/WEBP')
                return FileResponse(output, filename=f'processed_{file.name}', content_type='image/WEBP')
        return Response({'status': 'error'})

    def image_process(self, image_file: Image, settings: dict):
        image = Image.open(image_file)
        new_file_name = image_file.name.split('.')[0] + f'.{settings["format"]}'

        if settings['resolution']:
            high, width = image.size
            image = image.resize((settings['high'], settings['width']))

        image.save(OUTPUT_WORK_DIR / new_file_name, quality=settings['quality'],
                   format=settings['format'].upper())
        image = Image.open(OUTPUT_WORK_DIR / new_file_name)
        return image

    def zip_processing(self, file):
        pass