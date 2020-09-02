from rest_framework import serializers
from goods.models import SPU,Brand,GoodsCategory

# 频道分组
class GoodCateSimpleModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = GoodsCategory
        fields = [
            'id',
            'name'
        ]

# 定义品牌Brand序列化器
class BrandSimpleModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = Brand
        fields = [
            'id',
            'name'
        ]


# spu主表
class SPUModelSerializer(serializers.ModelSerializer):
    brand = serializers.StringRelatedField()
    brand_id = serializers.IntegerField()
    category1_id = serializers.IntegerField()
    category2_id = serializers.IntegerField()
    category3_id = serializers.IntegerField()

    class Meta:
        model = SPU
        exclude = [
            'category1',
            'category2',
            'category3',
        ]