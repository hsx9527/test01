from rest_framework import serializers
from goods.models import SpecificationOption,SPUSpecification

# 自定义查询集,暂时覆盖原来表中数据
class OptSpecSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SPUSpecification
        fields = [
            'id',
            'name'
        ]

# 规格选项表
class OptionModelSerializer(serializers.ModelSerializer):
    spec = serializers.StringRelatedField()
    spec_id = serializers.IntegerField()

    class Meta:
        model = SpecificationOption
        fields = [
            'id',
            'value',
            'spec',
            'spec_id'
        ]