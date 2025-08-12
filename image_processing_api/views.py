import datetime
import os.path
from zipfile import ZipFile
from datetime import datetime, date
from time import perf_counter

from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import default_storage

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import APIException
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
        # start_time = perf_counter()
        if serializer.is_valid():
            try:
                file = request.FILES['file']
            except:
                pass
            # default_storage.save(f'upload\\{file.name}', ContentFile(file.read())) # сохранение входящего файла
            # если zip файл вызываем метод zip_processing
            if file.name.lower().endswith('.zip'):
                datetime_name_mark = f'{date.today()}-{datetime.today().hour}-{datetime.today().minute}-{datetime.today().second}-{datetime.today().microsecond}'
                output_zip_filename = f'output_{datetime_name_mark}.zip'
                path = os.path.join(settings.MEDIA_ROOT, f'download\\{output_zip_filename}')
                if self.zip_processing(file, serializer.validated_data, path, datetime_name_mark):
                    file_url = request.build_absolute_uri(
                        os.path.join(settings.MEDIA_URL, f'download/{output_zip_filename}'))
                    # print(perf_counter() - start_time)
                    return Response({'status_code': status.HTTP_200_OK, 'file_url': file_url})
            # если изображение вызываем метод image_process
            elif file.name.lower().endswith(('.png', '.webp', '.jpg', '.jpeg')):
                path = os.path.join(settings.MEDIA_ROOT, 'download')
                new_filename = self.image_process(file, serializer.validated_data,
                                                  path)  # вызов функции обработки изображения
                file_url = request.build_absolute_uri(os.path.join(settings.MEDIA_URL, f'download/{new_filename}'))
                # print(perf_counter() - start_time)
                return Response({'status_code': status.HTTP_200_OK, 'file_url': file_url})
                # return FileResponse(output, filename=f'processed_{file.name}', content_type='image/WEBP')
        print(serializer.errors)
        return Response({'status_code': status.HTTP_400_BAD_REQUEST, 'message': 'Неверные параметры запроса'})

    def image_process(self, image_file: Image, inp_settings: dict, path) -> str:
        """Обрабатывает изображения.

        :param image_file: файл изображения
        :param inp_settings: файл с параметрами обработки изображения (request.POST)
        :param path: путь по которому следует сохранить файл
        :return: имя обработанного изображения
        """
        image = Image.open(image_file)

        if not inp_settings['resolution']:  # если False то меняем разрешение
            if inp_settings['proportion']:  # если True сохраняем пропорции
                width, high = image.size
                aspect_ratio = width / high  # считаем соотношение сторон
                # если False редактируется высота
                if not inp_settings['toggle_switch']:
                    image = image.resize((int(inp_settings['high'] / aspect_ratio), inp_settings['high']))
                # если True редактируется ширина
                else:
                    image = image.resize((inp_settings['width'], int(inp_settings['width'] * aspect_ratio)))
            else:
                image = image.resize((inp_settings['width'], inp_settings['high']))
        # если меняем формат
        if inp_settings['format']:
            # сохраняём в качестве quality и формате format
            datetime_name_mark = f'{date.today()}-{datetime.today().hour}-{datetime.today().minute}-{datetime.today().second}-{datetime.today().microsecond}'
            new_file_name = datetime_name_mark + image_file.name.split('.')[0] + f'.{inp_settings["format"]}'
            image.save(os.path.join(path, f'{new_file_name}'), quality=inp_settings['quality'],
                       format=inp_settings['format'].upper())
        # если формат оставить исходным
        else:
            image.save(os.path.join(path, image_file.name), quality=inp_settings['quality'],
                       format=inp_settings['format'].upper())
        image.close()
        # image = Image.open(os.path.join(settings.MEDIA_ROOT, f'download\\{new_file_name}'))
        return f'{datetime_name_mark}+{new_file_name}'

    def zip_processing(self, file, inp_settings: dict, path, datetime_name_mark) -> bool:
        """
        Обрабатывает изображения внутри zip-файла
        :param file: zip-файл
        :param inp_settings: файл с параметрами обработки изображения (request.POST)
        :param path: путь, по которому следует сохранить zip-файл с обработанными изображениями
        :param datetime_name_mark: тег даты-времени для формирования имени файла
        :return: булево значение - обработка успешна (True), обработка закончилась ошибкой (False)
        """
        # pillow не имеет формата jpg, меняем строку на jpeg
        if inp_settings['format'].lower() == 'jpg':
            inp_settings['format'] = 'jpeg'

        # открываем загруженный файл для чтения, открываем новый зип файл по маршруту path для записи
        with ZipFile(file) as zip_file, ZipFile(
                path, 'w') as output_zipfile:
            # проверяем есть ли изображения в файле
            if [file.filename for file in zip_file.infolist() if
                file.filename.lower().endswith(('.png', '.webp', '.jpg', '.jpeg'))]:
                os.mkdir(os.path.join(settings.MEDIA_ROOT,
                                      f'download\\output_zip_images\\{datetime_name_mark}'))  # создаём директорию для извлечения изображений
                dir_path_to_save = os.path.join(settings.MEDIA_ROOT,
                                                f'download\\output_zip_images\\{datetime_name_mark}')  # запоминаем путь по которому следует сохранять изображения
                for file_in_zip in zip_file.infolist():
                    if file_in_zip.filename.lower().endswith(('.png', '.webp', '.jpg', '.jpeg')):
                        with zip_file.open(file_in_zip.filename) as image_file:
                            image = Image.open(image_file)
                            if inp_settings[
                                'format'].lower() == 'jpeg' and image.mode == 'RGBA':  # jpeg не поддерживает rgba
                                image = image.convert('RGB')
                            new_file_name = image_file.name.split('/')[-1].split('.')[0]  # извлекаем имя файла
                            image.save(os.path.join(dir_path_to_save,
                                                    f'{new_file_name}.{inp_settings["format"].lower()}'),
                                       format=inp_settings['format'])  # пересохраняем с требуемым форматом
                for output_image in os.scandir(dir_path_to_save):
                    self.image_process(output_image, inp_settings, dir_path_to_save)
                    output_zipfile.write(output_image.path, output_image.name)
                return True
        return False
