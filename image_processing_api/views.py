import datetime
import os
from zipfile import ZipFile
from datetime import datetime, date
from time import perf_counter

import cairosvg
from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import default_storage

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from rest_framework import status

from PIL import Image
from cairosvg import svg2png

import io

from .serializers import InputImage


def index(request):
    return render(request, 'index.html')


class ImageProcessing(APIView):
    def get(self, request):
        print(request.data)
        return Response(request.method)

    def post(self, request):
        datetime_name_mark = f'{date.today()}-{datetime.today().hour}-{datetime.today().minute}-{datetime.today().second}-{datetime.today().microsecond}'
        serializer = InputImage(data=request.data)
        # start_time = perf_counter()
        if serializer.is_valid():
            try:
                file = request.FILES['file']
            except:
                raise APIException(code=status.HTTP_400_BAD_REQUEST, detail='Файл не найден')
            # default_storage.save(f'upload\\{file.name}', ContentFile(file.read())) # сохранение входящего файла
            # если zip файл вызываем метод zip_processing
            if file.name.lower().endswith('.zip'):
                output_zip_filename = f'output_{datetime_name_mark}.zip'
                path = os.path.join(settings.MEDIA_ROOT, f'download\\{output_zip_filename}')
                if self.zip_processing(file, serializer.validated_data, path, datetime_name_mark):
                    file_url = request.build_absolute_uri(
                        os.path.join(settings.MEDIA_URL, f'download/{output_zip_filename}'))
                    # print(perf_counter() - start_time)
                    return Response({'status_code': status.HTTP_200_OK, 'file_url': file_url})
            # если изображение вызываем метод image_process
            elif file.name.lower().endswith(('.png', '.webp', '.jpg', '.jpeg', '.eps', '.svg')):
                path = os.path.join(settings.MEDIA_ROOT, 'download')
                new_filename = f"{datetime_name_mark}{self.image_process(file, serializer.validated_data, path, 'single_image', datetime_name_mark)}"  # вызов функции обработки изображения
                file_url = request.build_absolute_uri(os.path.join(settings.MEDIA_URL, f'download/{new_filename}'))
                # print(perf_counter() - start_time)
                return Response({'status_code': status.HTTP_200_OK, 'file_url': file_url})
                # return FileResponse(output, filename=f'processed_{file.name}', content_type='image/WEBP')
        return Response({'status_code': status.HTTP_400_BAD_REQUEST, 'message': 'Неверные параметры запроса'})

    def image_process(self, image_file: Image, inp_settings: dict, path, tag: str, datetime_name_mark=None) -> str:
        """Обрабатывает изображения.

        :param image_file: файл изображения
        :param inp_settings: файл с параметрами обработки изображения (request.POST)
        :param path: путь по которому следует сохранить файл
        :param tag: тег для формирования имени файла, если zip то без временной метки, иначе с ней
        :return: имя обработанного изображения
        """
        # если получен файл зип, осталвляем только имя файла
        if '/' in image_file.name:
            file_name = image_file.name.split('/')[-1]
        else:
            file_name = image_file.name
        # если меняем формат
        if inp_settings['format']:
            # сохраняём в качестве quality и формате format
            new_file_name = file_name.split('.')[0] + f'.{inp_settings["format"]}'
        # если формат оставить исходным
        else:
            new_file_name = file_name

        if image_file.name.lower().endswith('.svg'):
            # если параметр vector False конвертируем в формат для обработки библиотекой pillow
            if not inp_settings['vector']:
                png_data = svg2png(file_obj=image_file)
                png_buffer = io.BytesIO(png_data)
                image = Image.open(png_buffer)
            # иначе сохраняем без изменений
            else:
                if tag == 'zip':
                    cairosvg.svg2svg(file_obj=image_file, write_to=os.path.join(path, file_name))
                else:
                    cairosvg.svg2svg(file_obj=image_file, write_to=os.path.join(path, datetime_name_mark + file_name))
                return image_file.name
        elif image_file.name.lower().endswith('.eps'):
            if not inp_settings['vector']:
                image = Image.open(image_file)
            else:
                if tag == 'zip':
                    default_storage.save(os.path.join(path, image_file.name), image_file)
                else:
                    # сохраняём файл из локального хранилища без изменений
                    default_storage.save(os.path.join(path, datetime_name_mark + image_file.name), image_file)
                return image_file.name
        else:
            image = Image.open(image_file)

        # pillow не имеет формата jpg, меняем строку на jpeg
        if inp_settings['format'].lower() == 'jpg':
            inp_settings['format'] = 'jpeg'
        # jpeg не поддерживает RGBA режим
        if image.mode == 'RGBA' and inp_settings['format'] == 'jpeg':
            image = image.convert('RGB')

        if not inp_settings['resolution']:  # если False то меняем разрешение
            if inp_settings['proportion']:  # если True сохраняем пропорции
                width, high = image.size
                aspect_ratio = width / high  # считаем соотношение сторон
                # если False редактируется высота
                if not inp_settings['toggle_switch']:
                    image = image.resize((int(inp_settings['high'] * aspect_ratio), inp_settings['high']))
                # если True редактируется ширина
                else:
                    image = image.resize((inp_settings['width'], int(inp_settings['width'] / aspect_ratio)))
            else:
                image = image.resize((inp_settings['width'], inp_settings['high']))
        if tag == 'zip':
            image.save(os.path.join(path, new_file_name), quality=inp_settings['quality'],
                       format=inp_settings['format'].upper())
        elif tag == 'single_image':
            image.save(os.path.join(path, datetime_name_mark + new_file_name), quality=inp_settings['quality'],
                       format=inp_settings['format'].upper())
        image.close()
        # image = Image.open(os.path.join(settings.MEDIA_ROOT, f'download\\{new_file_name}'))
        return f'{new_file_name}'

    def zip_processing(self, file, inp_settings: dict, path, datetime_name_mark) -> bool:
        """
        Обрабатывает изображения внутри zip-файла
        :param file: zip-файл
        :param inp_settings: файл с параметрами обработки изображения (request.POST)
        :param path: путь, по которому следует сохранить zip-файл с обработанными изображениями
        :param datetime_name_mark: тег даты-времени для формирования имени файла
        :return: булево значение - обработка успешна (True), обработка закончилась ошибкой (False)
        """

        # открываем загруженный файл для чтения, открываем новый зип файл по маршруту path для записи
        with ZipFile(file) as zip_file, ZipFile(
                path, 'w') as output_zipfile:
            # проверяем есть ли изображения в файле
            if [file.filename for file in zip_file.infolist() if
                file.filename.lower().endswith(('.png', '.webp', '.jpg', '.jpeg', '.svg'))]:
                os.mkdir(os.path.join(settings.MEDIA_ROOT,
                                      f'download\\output_zip_images\\{datetime_name_mark}'))  # создаём директорию для извлечения изображений
                dir_path_to_save = os.path.join(settings.MEDIA_ROOT,
                                                f'download\\output_zip_images\\{datetime_name_mark}')  # запоминаем путь по которому следует сохранять изображения
                for file_in_zip in zip_file.infolist():
                    if file_in_zip.filename.lower().endswith(('.png', '.webp', '.jpg', '.jpeg', '.svg')):
                        with zip_file.open(file_in_zip.filename) as image_file:
                            self.image_process(image_file, inp_settings, dir_path_to_save, 'zip')
                for output_image in os.scandir(dir_path_to_save):
                    output_zipfile.write(output_image.path, output_image.name)
                return True
        return False
