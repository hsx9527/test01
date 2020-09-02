from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ModelViewSet
from meiduo_admin.serializers.spu_serializers import *
from meiduo_admin.custom_pagination import MyPage

# 频道三个等级分类
class GoodsCateSimpleView(ListAPIView):
    queryset = GoodsCategory.objects.all()
    serializer_class = GoodCateSimpleModelSerializer

    def get_queryset(self):
        # 如果路径中有pk，则根据pk过滤出2、3级分类
        cat_id = self.kwargs.get('pk')

        if cat_id:
            return self.queryset.filter(parent_id=cat_id)

        return self.queryset.filter(parent=None)



# 品牌表处理函数
class BrandSimpleView(ListAPIView):
    queryset = Brand.objects.all()
    serializer_class = BrandSimpleModelSerializer


# spu管理
class SPUView(ModelViewSet):
    queryset = SPU.objects.all()
    serializer_class = SPUModelSerializer
    pagination_class = MyPage

    def get_queryset(self):
        # 通过self对象在非视图函数中获取请求对象
        keyword = self.request.query_params.get('keyword')
        if keyword:
            return self.queryset.filter(name__contains=keyword)
        return self.queryset.all()