from django.shortcuts import render, get_object_or_404
from django.db.utils import IntegrityError
from rest_framework.response import Response
from rest_framework.exceptions import status
from rest_framework.views import APIView
from .serializers import ProviderParameters, NewSegment, GetProcess, GetChields
from .models import Metric, RegionCodifier, OKPD2Codifier, Segment, OKPD2, Process
import json
from time import perf_counter


# Create your views here.
class ProviderStatistic(APIView):
    def get(self, request):
        """
        Выдаёт статус выполнения существующего запроса (% выполнения | file_url)
        """
        request_param = GetProcess(data=request.data)
        if request_param.is_valid():
            request_id = request_param.validated_data['request_id']
            process = get_object_or_404(Process, pk=request_id)
            return Response({'status_code': status.HTTP_200_OK,
                             'progress': process.progress,
                             'file_url': process.data_file,
                             'message': 'Успех'})
        else:
            return Response({'status_code': status.HTTP_400_BAD_REQUEST, 'message': 'Ошибка валидации параметров'})

    def post(self, request):
        """
        Конечная точка для создания процесса (задачу) сбора статистики
        """
        parameters = ProviderParameters(data=request.data)
        if parameters.is_valid():
            okpd2_codifier_ids, metrics, region_ids, segment = parameters.validated_data.values()
            okpd2_codifier_obj = [OKPD2Codifier.objects.get(pk=ids) for ids in okpd2_codifier_ids]
            okpd2_obj = [OKPD2.objects.get(code=okpd_codifier.code) for okpd_codifier in okpd2_codifier_obj]
            okpd2_ids = [obj.id for obj in okpd2_obj]
            process = Process()
            process.okpd2_ids = okpd2_ids
            process.region_ids = region_ids
            process.metrics = metrics
            process.save()
            request_id = process.pk
            return Response({'status_code': status.HTTP_200_OK, 'request_id': request_id, 'message': 'Успех'})
        else:
            print(parameters.errors)
            return Response({'status_code': status.HTTP_400_BAD_REQUEST, 'message': 'Ошибка валидации параметров'})


class GetMetricsRegions(APIView):
    def get(self, request):
        """
        Выдаёт метрики и регионы из БД
        """
        raw_metrics = Metric.objects.all()
        raw_regions = RegionCodifier.objects.all()
        metrics = [{'id': m.id, 'metric_name': m.name} for m in raw_metrics]
        regions = [{'region_code': r.region_code, 'name': r.region_name, 'region_id': r.region_id} for r in raw_regions]
        result = {'metrics': metrics, 'regions': regions}
        with open('response_metrics+regions.json', 'w', encoding='utf-8') as jsonfile:
            json.dump(result, jsonfile, ensure_ascii=False, indent=4)
        return Response(result)


class GetOkpd2Segments(APIView):
    def get(self, request):
        """
        Выдаёт ОКПД2-коды и пользовательские сегменты из БД
        """
        t_start = perf_counter()
        raw_okpd_queryset = OKPD2Codifier.objects.all()
        result = {
            'segments': [{'id': segment.id, 'name': segment.name,
                          'okpd2_codes': [okpd2.code for okpd2 in segment.okpd2_set.all()]} for segment in
                         Segment.objects.all()],
            'okpd2': [{'id': okpd.id, 'code': okpd.code, 'description': okpd.description} for okpd in
                      raw_okpd_queryset.filter(parent_id=0)],
        }
        """self.children_placeholder(result['okpd2'], raw_okpd_queryset)"""
        with open('response_segments+okpd.json', 'w', encoding='utf-8') as jsonfile:
            json.dump(result, jsonfile, ensure_ascii=False, indent=4)
        print('Время выполнения:', (perf_counter() - t_start) // 60, 'мин :', (perf_counter() - t_start) % 60, 'сек')
        return Response(result)

    def children_placeholder(self, base_layer, raw_okpd_queryset, count=0):
        """
        Заполняет массив children для каждого объекта ОКПД2-кода начиная с базового (parent_id=0) уровня
        """
        for d in base_layer:
            chields = raw_okpd_queryset.filter(parent_id=d['id'])
            if chields:
                new_chields = list(
                    {'id': item.id, 'code': item.code, 'desctiprion': item.description, 'chields': []} for item in
                    chields)
                d['chields'].extend(new_chields)
                self.children_placeholder(new_chields, raw_okpd_queryset)
        return count


class GetChieldForOkpd2(APIView):
    def get(self, request):
        okpd_data = GetChields(data=request.data)
        if okpd_data.is_valid():
            chields = OKPD2Codifier.objects.filter(parent_id=okpd_data.validated_data['parent_id'])
            result = [{'id': okpd.id, 'code': okpd.code, 'description': okpd.description} for okpd in chields]
            with open('response_okpd2_chields.json', 'w', encoding='utf-8') as jsonfile:
                json.dump(result, jsonfile, ensure_ascii=False, indent=4)
            return Response(result)
        else:
            return Response({'status_code': status.HTTP_400_BAD_REQUEST, 'message': 'Ошибка валидации параметров'})


class CreateSegment(APIView):
    def post(self, request):
        """
        конечная точка для создания сегмента
        """
        segment_data = NewSegment(data=request.data)
        try:
            if segment_data.is_valid():
                segment_name, okpd2_array = segment_data.validated_data.values()
                segment = Segment.objects.create(name=segment_name)
                okpd2_objects_for_id = [OKPD2Codifier.objects.get(pk=i) for i in okpd2_array]
                for i in okpd2_objects_for_id:
                    segment.okpd2_set.add(OKPD2.objects.get(code=i.code))
                return Response({'status_code': status.HTTP_200_OK, 'message': 'Успех'})
            else:
                return Response({'status': status.HTTP_400_BAD_REQUEST,
                                 'message': 'Ошибка заполнения параметров запроса'})
        except IntegrityError as e:
            return Response({'status': status.HTTP_400_BAD_REQUEST, 'message': 'Имя сегмента уже существует'})
