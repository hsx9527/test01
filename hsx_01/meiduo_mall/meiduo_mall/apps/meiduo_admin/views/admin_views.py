from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ModelViewSet
from meiduo_admin.serializers.admin_serializers import *
from meiduo_admin.custom_pagination import MyPage

# 组表视图
class AdminGroupView(ListAPIView):
    queryset = Group.objects.all()
    serializer_class = AdminGroupModelSerializer

# 用户表之管理员视图
class AdminView(ModelViewSet):
    queryset = User.objects.filter(is_staff=True)
    serializer_class = AdminModelSerializer

    pagination_class = MyPage