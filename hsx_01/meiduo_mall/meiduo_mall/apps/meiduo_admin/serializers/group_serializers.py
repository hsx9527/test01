
from rest_framework import serializers
from django.contrib.auth.models import Group,Permission
# 权限表
class GroupPermSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permission
        fields = [
            'id',
            'name'
        ]

# 分组表
class GroupModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = [
            'id',
            'name',

            'permissions'
        ]