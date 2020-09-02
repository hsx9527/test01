from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ModelViewSet
from meiduo_admin.serializers.perm_serializers import *
from meiduo_admin.custom_pagination import MyPage

# 内置类ContentType视图
class PermContentTypeView(ListAPIView):
    queryset = ContentType.objects.all()
    serializer_class = PermContentTypeModelSerializer

# 权限表视图
class PermView(ModelViewSet):
    queryset = Permission.objects.all()
    serializer_class = PermModelSerializer

    pagination_class = MyPage

    def get_queryset(self):
        return self.queryset.order_by('id')