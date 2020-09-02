from rest_framework.generics import ListAPIView
from rest_framework.viewsets import ModelViewSet
from meiduo_admin.serializers.image_serializers import *
from meiduo_admin.custom_pagination import MyPage

# sku表
class SKUSimpleView(ListAPIView):
    queryset = SKU.objects.all()
    serializer_class = SKUSimpleModelSerializer

# sku_image表
class ImageView(ModelViewSet):
    queryset = SKUImage.objects.all()
    serializer_class = ImageModelSerializer

    pagination_class = MyPage