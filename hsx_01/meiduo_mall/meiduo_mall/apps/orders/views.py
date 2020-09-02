from django.shortcuts import render
from django.views import View
from meiduo_mall.utils.views import login_required
from django.utils.decorators import method_decorator
from django_redis import get_redis_connection
from goods.models import SKU
from users.models import Address
from django.http import JsonResponse
import json
from decimal import Decimal
from .models import *
from meiduo_mall.utils.views import login_required
from django.utils.decorators import method_decorator
# timezone:是django提供的一个专门用于处理时间的模块
from django.utils import timezone
from django.db import transaction
# Create your views here.


# 提交订单处理函数
class OrderCommitView(View):
    @method_decorator(login_required)
    def post(self, request):
        # 1、提取参数
        data = json.loads(request.body.decode())
        address_id = data.get('address_id')
        pay_method = data.get('pay_method')

        # 2、校验参数
        if not all([address_id, pay_method]):
            return JsonResponse({'code': 400, 'errmsg': '缺少参数'}, status=400)
        try:
            address = Address.objects.get(pk=address_id)
        except Address.DoesNotExist as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '地址有误！'}, status=404)

        if pay_method not in [1,2]:
            return JsonResponse({'code': 400, 'errmsg': '不支持的付款方式'}, status=400)


        # 3、新建/保存数据(新建订单和订单商品数据)
        # 3.1 新建订单表数据(主)
        # 保证订单id的唯一
        # order_id = "202008060901560001"
        #
        # timezone.localtime() --> 本地时间点对象(取决于TIME_ZONE配置参数)
        user = request.user
        order_id = timezone.localtime().strftime("%Y%m%d%H%M%S") + "%09d"%user.id

        # 获取用户的购物车sku商品
        conn = get_redis_connection('carts')
        # {b'1': b'4'}
        cart_redis = conn.hgetall('carts_%s'%user.id)
        # [b'1']
        selected_redis = conn.smembers('selected_%s'%user.id)
        carts = {} # 保存当前已选中的sku商品信息
        for k,v in cart_redis.items():
            # k: b'1'; v:b'4'
            if k in selected_redis:
                carts[int(k)] = int(v) # carts[1]=4

        # 3.2 新建订单商品数据(从)
        sku_ids = carts.keys() # 选中的购物车中的所有sku的主键

        with transaction.atomic():
            # 关键的时间阶段——order订单新建节点
            save_id = transaction.savepoint() # 事务执行保存点

            order = OrderInfo.objects.create(
                order_id=order_id,
                user=user,
                address=address,
                total_count=0,  # 后续在统计订单商品的时候再修改
                total_amount=0,
                freight=Decimal('10.00'),
                pay_method=pay_method,
                # status= 2 if pay_method==1 else 1
                status=OrderInfo.ORDER_STATUS_ENUM['UNSEND'] if pay_method == OrderInfo.PAY_METHODS_ENUM['CASH'] else
                OrderInfo.ORDER_STATUS_ENUM['UNPAID']
            )

            for sku_id in sku_ids:

                while True:
                    sku = SKU.objects.get(pk=sku_id)
                    # 旧数据
                    old_stock = sku.stock
                    old_sales = sku.sales
                    if carts[sku_id] > old_stock:
                        # 由于库存不足，我事务需要会滚到，订单新建之前的节点
                        transaction.savepoint_rollback(save_id)
                        return JsonResponse({'code': 400, 'errmsg': '库存不足！'}, status=400)

                    # 商品销量和库存修改
                    # sku.stock -= carts[sku_id]
                    # sku.sales += carts[sku_id]
                    # sku.save()

                    # 计算新值——此处的计算，可能很漫长，期间很有可能别的事务介入
                    new_stock = old_stock - carts[sku_id]
                    new_sales = old_sales + carts[sku_id]

                    # 更新——在原有的旧数据基础上过滤更新
                    result = SKU.objects.filter(
                        pk=sku.id,
                        stock=old_stock,
                        sales=old_sales
                    ).update(stock=new_stock, sales=new_sales)
                    if result == 0:
                        continue
                    break

                # 插入一个订单商品数据
                OrderGoods.objects.create(
                    order=order,
                    sku=sku,
                    count=carts[sku_id],
                    price=sku.price
                )

                # 订单表数据修改
                order.total_count += carts[sku_id]
                order.total_amount += (carts[sku_id] * sku.price)
            # 每一次插入订单商品的时候修改了当前订单的属性
            order.total_amount += order.freight
            order.save()
            transaction.savepoint_commit(save_id) # 删除保存点

        # 把用户的购车车商品删除
        conn.hdel('carts_%s'%user.id, *sku_ids)
        conn.srem('selected_%s'%user.id, *sku_ids)

        # 4、构建响应
        return JsonResponse({'code': 0, 'errmsg': 'ok', 'order_id': order_id})



# 订单结算接口
class OrderSettlementView(View):

    @method_decorator(login_required)
    def get(self, request):
        user = request.user
        # 1、读取用户购物商品(必须是选中的！)
        conn = get_redis_connection('carts')
        # {b'1': b'4'}
        cart_redis = conn.hgetall('carts_%s'%user.id)
        # [b'1']
        cart_selected = conn.smembers('selected_%s'%user.id)

        # 构造商品返回数据
        sku_list = []
        for k,v in cart_redis.items():
            # k:b'1'; v:b'4'
            if k in cart_selected:
                sku = SKU.objects.get(pk=k)
                sku_list.append({
                    'id': sku.id,
                    'name': sku.name,
                    'default_image_url': sku.default_image_url.url,
                    'price': sku.price,
                    'count': int(v)
                })

        # 2、读取用户的收货地址数据
        addresss_list = []
        addresses = Address.objects.filter(user=user)
        for address in addresses:
            if not address.is_deleted:
                addresss_list.append({
                      "id": address.id,
                      "province": address.province.name,
                      "city": address.city.name,
                      "district": address.district.name,
                      "place": address.place,
                      "mobile": address.mobile,
                      "receiver": address.receiver,
                })

        # 3、构建响应数据
        # freight = 10.0
        # 结论：使用Decimal类型来保存十进制数，目的是为了保证计算的精确度！
        freight = Decimal('10.5')

        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'context': {
                'addresses': addresss_list,
                'skus': sku_list,
                'freight': freight
            }
        })