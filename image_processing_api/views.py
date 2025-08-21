import datetime
import os
from zipfile import ZipFile
from datetime import datetime, date
from time import perf_counter
import subprocess
import tempfile

import cairosvg
from django.shortcuts import render
from django.conf import settings
from django.core.files.storage import default_storage

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.exceptions import APIException
from rest_framework import status

from PIL import Image
from cairosvg import svg2png, svg2svg

import io

from .serializers import InputImage
from .minio_bucket import bucket





class ImageProcessing(APIView):
    def get(self, request):
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
                        os.path.join(settings.MEDIA_URL, f'download/{output_zip_filename}')) # стандартная ссылка в файловой системе сервера"""
                    # print(perf_counter() - start_time) # оценка времени выполнения

                    """ Раскоментить если подключается S3-хранилище
                    bucket.upload_file('backet-test', f'zipfiles/{output_zip_filename}',
                                       os.path.join(settings.MEDIA_ROOT,
                                                    f"download/{output_zip_filename}"))  # отправка файла в S3
                    os.remove(os.path.join(settings.MEDIA_ROOT, f"download/{output_zip_filename}"))  # удаляем файл с сервера
                    file_url = bucket.share_file_from_bucket('backet-test',
                                                             f'zipfiles/{output_zip_filename}')  # ссылка на S3-хранилище"""

                    return Response({'status_code': status.HTTP_200_OK, 'file_url': file_url, 'file_name': output_zip_filename})
            # если изображение вызываем метод image_process
            elif file.name.lower().endswith(('.png', '.webp', '.jpg', '.jpeg', '.eps', '.svg', 'ai')):
                path = os.path.join(settings.MEDIA_ROOT, 'download')
                new_filename = f"{datetime_name_mark}{self.image_process(file, serializer.validated_data, path, 'single_image', datetime_name_mark)}"  # вызов функции обработки изображения
                file_url = request.build_absolute_uri(os.path.join(settings.MEDIA_URL,
                                                                   f'download/{new_filename}'))  # стандартная ссылка в файловой системе сервера"""

                """ Раскоментить если подключается S3-хранилище
                bucket.upload_file('backet-test', f'images/{new_filename}',
                                   os.path.join(settings.MEDIA_ROOT, f'download/{new_filename}'))  # отправка файла в S3
                os.remove(os.path.join(settings.MEDIA_ROOT, f'download/{new_filename}'))  # удаление файла с сервера (для S3-хранилища)
                file_url = bucket.share_file_from_bucket('backet-test', f'images/{new_filename}') # получение ссылки на файл из S3-хранилища"""

                # print(perf_counter() - start_time) # оценка времени выполнения
                return Response({'status_code': status.HTTP_200_OK, 'file_url': file_url, 'file_name': new_filename})
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

        file_name = image_file.name
        # формирование имени файла c новым форматом
        # если формат остаётся исходным
        if inp_settings['format'] == 'original':
            new_file_name = image_file.name
        # если меняем формат
        else: #inp_settings['format']:
            # если пришла одиночная картинка
            if tag == 'single_file':
                # имя файла в формате "format"
                new_file_name = file_name.split('.')[0] + f'.{inp_settings["format"]}'
            # если zip-файл
            else:
                if image_file.name.endswith('.svg'):
                    # проверяем, требуется ли преобразовать svg в растровый тип
                    if not inp_settings['vector']:
                        new_file_name = image_file.name[:image_file.name.find('.svg')] + '.' + inp_settings['format']
                    else:
                        new_file_name = image_file.name
                elif image_file.name.endswith('.eps'):
                    new_file_name = image_file.name
                # если растровый формат
                else:
                    new_file_name = file_name[:file_name.find(file_name.split('.')[-1])] + inp_settings['format']
        # преобразование векторного изображения в растровое
        if image_file.name.endswith('.svg'):
            # если параметр vector False конвертируем в формат для обработки библиотекой pillow
            if not inp_settings['vector'] and inp_settings['format'] != 'original':
                png_data = svg2png(file_obj=image_file)
                png_buffer = io.BytesIO(png_data)
                image = Image.open(png_buffer)
            # иначе сохраняем без изменений
            else:
                if tag == 'zip':
                    os.makedirs(os.path.join(path, '/'.join(image_file.name.split('/')[:-1])), exist_ok=True)
                    cairosvg.svg2svg(file_obj=image_file, write_to=os.path.join(path, new_file_name))
                else:
                    cairosvg.svg2svg(file_obj=image_file, write_to=os.path.join(path, datetime_name_mark + file_name))
                return image_file.name
        elif image_file.name.lower().endswith('.eps'):
            if tag == 'zip':
                os.makedirs(os.path.join(path, '/'.join(image_file.name.split('/')[:-1])), exist_ok=True)
                default_storage.save(os.path.join(path, image_file.name), image_file)
            else:
                # сохраняём файл из локального хранилища без изменений
                default_storage.save(os.path.join(path, datetime_name_mark + image_file.name), image_file)
            return image_file.name
        else:
            image = Image.open(image_file)

        # pillow не имеет формата jpg, меняем строку на jpeg
        if new_file_name.split('.')[-1].lower() == 'jpg':
            new_file_name = new_file_name[:new_file_name.find('jpg')] + 'jpeg'
        # jpeg не поддерживает RGBA режим
        if image.mode == 'RGBA' and new_file_name.split('.')[-1].lower() == 'jpeg':
            image = image.convert('RGB')

        if not inp_settings['resolution']:  # если False то меняем разрешение
            if inp_settings['proportion']:  # если True сохраняем пропорции
                width, high = image.size
                aspect_ratio = width / high  # считаем соотношение сторон
                # если False редактируется высота
                if not inp_settings['toggle_switch']:
                    image = image.resize((int(inp_settings['height'] * aspect_ratio), inp_settings['height']))
                # если True редактируется ширина
                else:
                    image = image.resize((inp_settings['width'], int(inp_settings['width'] / aspect_ratio)))
            else:
                image = image.resize((inp_settings['width'], inp_settings['height']))
        if tag == 'zip':
            os.makedirs(os.path.join(path, '/'.join(new_file_name.split('/')[:-1])), exist_ok=True)
            image.save(os.path.join(path, new_file_name), quality=inp_settings['quality'],
                        format=new_file_name.split('.')[-1])
        elif tag == 'single_image':
            image.save(os.path.join(path, datetime_name_mark + new_file_name), quality=inp_settings['quality'],
                       format=new_file_name.split('.')[-1])
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
                file.filename.lower().endswith(('.png', '.webp', '.jpg', '.jpeg', '.svg', '.eps'))]:
                dir_path_to_save = os.path.join(settings.MEDIA_ROOT,
                                                f'download/output_zip_images/{datetime_name_mark}')  # запоминаем путь по которому следует сохранять изображения
                os.mkdir(dir_path_to_save)  # создаём директорию для извлечения изображений
                # извлекаем, обрабатываем, сохраняем изображения из zip
                for file_in_zip in zip_file.infolist():
                    if file_in_zip.filename.lower().endswith(('.png', '.webp', '.jpg', '.jpeg', '.svg', '.eps')):
                        with zip_file.open(file_in_zip.filename) as image_file:
                            self.image_process(image_file, inp_settings, dir_path_to_save, 'zip')
                for output_file in os.scandir(dir_path_to_save):
                    for img in self.extract_image_file(output_file):
                        # print(img.find(datetime_name_mark), '/'.join(img[img.find(datetime_name_mark):].split('\\')[1:]))
                        output_zipfile.write(img, '/'.join(img[img.find(datetime_name_mark):].split('\\')[1:]))
                    # output_zipfile.write(output_image.path, f"{output_image.name}")
                #self.clear_and_del_dir(dir_path_to_save) очистка директории output_zip_images (для S3-хранилища)
                return True
        return False

    def extract_image_file(self, file):
        """
        функция получает пути всех изображений из папки
        :param file: папка или файл, пути/путь которого необходимо извлечь
        :return: result - список путей изображений
        """
        result = []
        if file.is_dir():
            for i in os.scandir(file):
                if i.is_file():
                    result.append(i.path)
                else:
                    result.extend(self.extract_image_file(i))
        elif file.is_file():
            result.append(file.path)
        return result

    def clear_and_del_dir(self, path):
        """
        функция для удаления всех вложенных файлов и папок указанной директории
        :param path: путь к директории
        :return: None
        """
        if os.path.isdir(path):
            files = os.scandir(path)
            if files:
                for file in files:
                    if file.is_dir():
                        self.clear_and_del_dir(file.path)
                    else:
                        os.remove(file.path)
            else:
                os.rmdir(path)
        else:
            os.remove(path)
        os.rmdir(path)
