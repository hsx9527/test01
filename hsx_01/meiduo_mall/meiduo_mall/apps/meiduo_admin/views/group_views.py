from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ModelViewSet
from meiduo_admin.serializers.group_serializers import *
from meiduo_admin.custom_pagination import MyPage

# 权限列表视图
class GroupPermSimpleView(ListAPIView):
    queryset = Permission.objects.all()
    serializer_class = GroupPermSimpleSerializer

# 组表视图
class GroupView(ModelViewSet):
    queryset = Group.objects.all()
    serializer_class = GroupModelSerializer

    pagination_class = MyPage