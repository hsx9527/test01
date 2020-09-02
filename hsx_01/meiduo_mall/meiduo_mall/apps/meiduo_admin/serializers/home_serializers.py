from rest_framework import serializers
from goods.models import GoodsVisitCount
# 日商品分类调用
class GoodVistiModelSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = GoodsVisitCount
        fields = [
            'category', # 外键关联字段
            'count'
        ]