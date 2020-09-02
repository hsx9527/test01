"""
重写django存储后端，修改ImageField类型字段url属性输出的结果
"""

from rest_framework import serializers
from django.core.files.storage import Storage
from django.conf import settings
from fdfs_client.client import Fdfs_client

class FastDFSStorage(Storage):

    def open(self, name, mode='rb'):
        # 我们这里返回None，表示无需打开本地文件因为我们不把文件存储本地
        return None

    def save(self, name, content, max_length=None):
        conn = Fdfs_client('./meiduo_mall/utils/fastdfs/client.conf')
        file_data = content.read()#content: 文件对象
        res = conn.upload_by_buffer(file_data)
        if res is None:
            # 上传失败
            raise serializers.ValidationError('上传fdfs失败！')
        file_id = res['Remote file_id']#下标取值

        return file_id


    def url(self, name):
        return settings.FDFS_URL + name