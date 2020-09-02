from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from meiduo_admin.serializers.option_serializers import *
from meiduo_admin.custom_pagination import MyPage


# 规格选项表
class OptionView(ModelViewSet):
    queryset = SpecificationOption.objects.all()
    serializer_class = OptionModelSerializer
    pagination_class = MyPage

    def opt_specs(self, request):
        specs = SPUSpecification.objects.all()
        s = OptSpecSimpleSerializer(instance=specs, many=True)
        return Response(s.data)