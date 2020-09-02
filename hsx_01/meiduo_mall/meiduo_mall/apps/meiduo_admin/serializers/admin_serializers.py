from rest_framework import serializers
from users.models import User
from django.contrib.auth.models import Group
from django.contrib.auth.hashers import make_password

# 组表列表返回
class AdminGroupModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = [
            'id',
            'name'
        ]

# 用户表
class AdminModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            'id',
            'username',
            'email',
            'mobile',

            'password',
            'groups',
            'user_permissions'
        ]

        extra_kwargs = {
            'password': {'write_only': True}
        }

    # 重写新建部分代码validate,调用自定义validate
    def validate(self, attrs):
        # 1、密码加密；2、添加is_staff=True
        password = attrs.get('password')
        attrs['password'] = make_password(password)
        attrs['is_staff'] = True
        return attrs