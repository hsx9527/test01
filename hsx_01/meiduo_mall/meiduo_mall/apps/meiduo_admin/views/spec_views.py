from rest_framework.viewsets import ModelViewSet
from meiduo_admin.serializers.spec_serializers import *
from meiduo_admin.custom_pagination import MyPage


# 规格表处理函数
class SpecView(ModelViewSet):
    queryset = SPUSpecification.objects.all()
    serializer_class = SpecModelSerializer

    pagination_class = MyPage