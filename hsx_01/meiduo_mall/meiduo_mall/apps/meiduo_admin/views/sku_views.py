from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ModelViewSet
from meiduo_admin.serializers.sku_serializers import *
from meiduo_admin.custom_pagination import MyPage


#新增中的商品(规格表)
class SpecSimpleView(ListAPIView):
    queryset = SPUSpecification.objects.all()
    serializer_class = SpecModelSerializer

    def get_queryset(self):
        spu_id = self.kwargs.get('pk')
        return self.queryset.filter(spu_id=spu_id)


# 新增的可选种类spu
class SPUSimpleView(ListAPIView):
    queryset = SPU.objects.all()
    serializer_class = SPUSimpleSerializer


# 新增的可选三级分类
class SKUCateView(ListAPIView):
    queryset = GoodsCategory.objects.all()
    serializer_class = SKUCatSimpleSerialzier

    def get_queryset(self):
        return self.queryset.filter(parent_id__gt=37)


# SKU规格表
class SKUView(ModelViewSet):
    queryset = SKU.objects.all()
    serializer_class = SKUModelSerializer

    pagination_class = MyPage

    def get_queryset(self):
        keyword = self.request.query_params.get('keyword')
        if keyword:
            return self.queryset.filter(name__contains=keyword)
        return self.queryset.all()