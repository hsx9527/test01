from rest_framework import serializers
from django.contrib.auth.models import Permission,ContentType

# 内置函数类表:区别内容表
class PermContentTypeModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = ContentType
        fields = [
            'id',
            'name'
        ]

# 权限表(主)
class PermModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = [
            'id',
            'name',
            'codename',
            'content_type'
        ]