from rest_framework import serializers
from goods.models import SKUImage,SKU

# 在保存数据之前需要先获取图片关联的sku的id
class SKUSimpleModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKU
        fields = [
            'id',
            'name'
        ]


# 图片主处理函数
class ImageModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKUImage
        fields = [
            'id',
            'sku',
            'image' # 序列化器对ImageField类型字段序列化的结果取决于自定义的存储后端！！！
        ]
