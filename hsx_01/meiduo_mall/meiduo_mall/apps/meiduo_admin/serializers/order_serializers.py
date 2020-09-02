from rest_framework import serializers
from orders.models import OrderInfo,OrderGoods
from goods.models import SKU

# 商品表重写
class SKUSimpleModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SKU
        fields = [
            'name',
            'default_image_url'
        ]

# 中间关联表重写
class OrderGoodsModelSerializer(serializers.ModelSerializer):
    # 是单一的SKU模型类对象
    sku = SKUSimpleModelSerializer()

    class Meta:
        model = OrderGoods
        fields = [
            'count',
            'price',
            'sku'
        ]

# 详情订单重写
class OrderDetailModelSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()

    # 多个OrderGoods对象序列化
    skus = OrderGoodsModelSerializer(many=True)

    class Meta:
        model = OrderInfo
        fields = "__all__"


# 重写订单表信息(主表)
class OrderSimpleModelSerializer(serializers.ModelSerializer):
    # create_time = serializers.DateTimeField(format="%Y/%m/%d %H:%M:%S")
    class Meta:
        model = OrderInfo
        fields = [
            'order_id',
            'create_time'
        ]
        extra_kwargs = {
            'create_time': {'format': '%Y/%m/%d %H:%M:%S'}
        }