from minio import Minio
from minio.lifecycleconfig import LifecycleConfig, Rule, Expiration, Filter

from datetime import timedelta

DEFAULT_ENDPOINT_URL = 'localhost:9000'  # домен:порт (по-умолчанию для тестовой среды - localhost:9000)
DEFAULT_ACCESS_KEY = 'minioadmin'  # логин minio (по-умолчанию для тестовой среды - minioadmin)
DEFAULT_SECRET_KEY = 'minioadmin'  # пароль minio (по-умолчанию для тестовой среды - minioadmin)


class MyStorage:
    def __init__(self, endpoint: str, access_key: str, secret_key: str, secure: bool = False):
        self.client = Minio(
            endpoint=endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure  # отключение подключения по HTTPS
        )
        config = LifecycleConfig([Rule(rule_id='cleanup_dir_zipfiles', status="Enabled", expiration=Expiration(days=1),
                                       rule_filter=Filter(prefix='zipfiles/')),
                                  Rule(rule_id='cleanup_dir_images', status='Enabled', expiration=Expiration(days=1),
                                       rule_filter=Filter(prefix='images/'))])
        self.client.set_bucket_lifecycle('backet-test', config)
        print('Подключение к хранилищу успешно')

    def create_bucket(self, bucket_name):
        self.client.make_bucket(bucket_name)

    def delete_bucket(self, bucket_name):
        self.client.remove_bucket(bucket_name)

    def upload_file(self, bucket_name: str, file_name: str, file_path: str):
        """
        Загрузка файла в S3-хранилище
        :param bucket_name:
        :param file_name:
        :param file_path:
        :return: None
        """
        self.client.fput_object(bucket_name, file_name, file_path)

    def share_file_from_bucket(self, backet_name, file_name, expire=timedelta(seconds=60)):
        """
        Генерирует ссылку на скачивание файла
        :param backet_name:
        :param file_name:
        :param expire:
        :return:
        """
        return self.client.presigned_get_object(backet_name, file_name, expire)


storage = MyStorage(DEFAULT_ENDPOINT_URL, DEFAULT_ACCESS_KEY, DEFAULT_SECRET_KEY)