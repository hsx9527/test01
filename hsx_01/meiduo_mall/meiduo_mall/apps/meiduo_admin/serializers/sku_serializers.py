from rest_framework import serializers
from goods.models import SKU,SKUSpecification,GoodsCategory,SPU,SPUSpecification,SpecificationOption
from celery_tasks.html.tasks import generate_static_sku_detail_html
from django.db import transaction

#新增中的商品(序列化规格表)
class OptModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = SpecificationOption
        fields = [
            'id',
            'value'
        ]


#新增中的商品(序列化规格表)
class SpecModelSerializer(serializers.ModelSerializer):
    spu = serializers.StringRelatedField()
    spu_id = serializers.IntegerField()
    options = OptModelSerializer(many=True)

    class Meta:
        model = SPUSpecification
        fields = [
            'id',
            'name',
            'spu',
            'spu_id',
            'options'
        ]


# 新增中的SPU表序列化器
class SPUSimpleSerializer(serializers.ModelSerializer):
    class Meta:
        model = SPU
        fields = [
            'id',
            'name'
        ]


# 新增中的分类表序列化器
class SKUCatSimpleSerialzier(serializers.ModelSerializer):
    class Meta:
        model = GoodsCategory
        fields = [
            'id',
            'name'
        ]


# SKU规格表序列化器(从)
class SKUSpecModelSerializer(serializers.ModelSerializer):
    spec_id = serializers.IntegerField()
    option_id = serializers.IntegerField()

    class Meta:
        model = SKUSpecification
        fields = [
            'spec_id',
            'option_id'
        ]


# SKU表序列化器(主)
class SKUModelSerializer(serializers.ModelSerializer):

    spu = serializers.StringRelatedField()
    spu_id = serializers.IntegerField()
    # StringRelatedField是不作用于反序列化的！
    category = serializers.StringRelatedField()
    category_id = serializers.IntegerField()

    # 关联的模型类是：SKUSpecification; 从表多个对象
    specs = SKUSpecModelSerializer(many=True)

    class Meta:
        model = SKU
        fields = "__all__"

    def update(self, instance, validated_data):
        # 根据传入的specs规格和选项信息插入中间表数据
        specs = validated_data.pop('specs')

        with transaction.atomic():
            save_id = transaction.savepoint()

            try:
                # 更新主表数据
                SKU.objects.filter(pk=instance.id).update(**validated_data)
                # 更新中间数据
                # 1、删除原有的中间表数据
                SKUSpecification.objects.filter(sku_id=instance.id).delete()
                # 2、插入新的中间表数据
                for temp in specs:
                    # temp: {spec_id: "4", option_id: 8}
                    temp['sku_id'] = instance.id
                    SKUSpecification.objects.create(**temp)
            except Exception as e:
                transaction.savepoint_rollback(save_id)
                raise e

            transaction.savepoint_commit(save_id)

        generate_static_sku_detail_html.delay(instance.id)

        return instance

    def create(self, validated_data):
        specs = validated_data.pop('specs')
        # 默认的图片
        validated_data['default_image_url'] = "group1/M00/00/02/CtM3BVrRa8iAZdz1AAFZsBqChgk2188464"
        sku = None
        with transaction.atomic():
            save_id = transaction.savepoint()
            try:
                sku = SKU.objects.create(**validated_data)
                for temp in specs:
                    temp['sku_id'] = sku.id
                    SKUSpecification.objects.create(**temp)
            except Exception as e:
                transaction.savepoint_rollback(save_id)
                raise e
            transaction.savepoint_commit(save_id)
        generate_static_sku_detail_html.delay(sku.id)
        return sku