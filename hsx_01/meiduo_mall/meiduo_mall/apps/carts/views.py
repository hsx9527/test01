from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django_redis import get_redis_connection
import json
from .utils import carts_cookie_encode,carts_cookie_decode
from goods.models import SKU
# Create your views here.

# 首页购物车下拉展示
class CartsSimpleView(View):
    def get(self, request):
        user = request.user
        cart_dict = {} # 购物车数据——格式和cookie格式是一样的
        if user.is_authenticated:
            # 已登陆，从redis中读商品数据
            conn = get_redis_connection('carts')
            carts_redis = conn.hgetall('carts_%s'%user.id)
            carts_selected = conn.smembers('selected_%s'%user.id)
            for k,v in carts_redis.items():
                cart_dict[int(k)] = {
                    'count': int(v),
                    'selected': k in carts_selected
                }
        else:
            # 未登陆，从cookie中读商品数据
            cookie_str = request.COOKIES.get('carts')
            if cookie_str:
                cart_dict = carts_cookie_decode(cookie_str)

        # 构造响应数据
        cart_skus = []
        for k,v in cart_dict.items():
            # k: sku_id； v: {"count":xx, "selected":xxx}
            sku = SKU.objects.get(pk=k)
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': v['count'],
                'default_image_url': sku.default_image_url.url
            })

        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'cart_skus': cart_skus
        })


# 全选处理函数
class CartSelectAllView(View):
    # 设置全选/全取消
    def put(self, request):
        # 1、获取参数
        data = json.loads(request.body.decode())
        selected = data.get("selected") # True or False

        user = request.user
        if user.is_authenticated:
            # 已登陆:把所有的sku_id加入/删除到selected_user_id的集合中
            conn = get_redis_connection('carts')
            cart_dict = conn.hgetall('carts_%s'%user.id)
            # [b'1', b'2']
            sku_ids = cart_dict.keys()
            # 2、设置全/全取消
            if selected:
                conn.sadd('selected_%s'%user.id, *sku_ids)
            else:
                conn.srem('selected_%s'%user.id, *sku_ids)
            return JsonResponse({'code': 0, 'errmsg': 'ok'})

        else:
            # 未登陆
            # 1、cookie购物车
            cookie_str = request.COOKIES.get("carts")
            # {1: {count:xx, selected:xxx}, 2: {count:xxx, selected:xxx}}
            cart_dict = carts_cookie_decode(cookie_str)
            sku_ids = cart_dict.keys()
            for sku_id in sku_ids:
                cart_dict[sku_id]['selected'] = selected
            # 3、覆盖写入cookie购物车
            cookie_str = carts_cookie_encode(cart_dict)
            response = JsonResponse({'code': 0, 'errmsg': 'ok'})
            response.set_cookie('carts', cookie_str)
            return response


# 购物车处理函数
class CartsView(View):

    # 删除购物车
    def delete(self, request):
        # {"sku_id": xxx}}
        data = json.loads(
            request.body.decode()
        )
        sku_id = data.get('sku_id')

        user = request.user
        # 1、已登陆
        if user.is_authenticated:
            conn = get_redis_connection('carts')
            # 1.1 删除购物车哈希数据——carts_user_id :  {sku_id : count}
            conn.hdel('carts_%s'%user.id, sku_id)
            # 1.2 删除集合中的sku_id
            conn.srem('selected_%s'%user.id, sku_id)
            return JsonResponse({'code': 0, 'errmsg': 'ok'})
        # 2、未登陆
        else:
            # 2.1 获取cookie购物车数据
            cookie_str = request.COOKIES.get('carts')
            cart_dict = carts_cookie_decode(cookie_str)
            # 2.2 删除cookie购物车字典中的sku_id键值对
            if sku_id in cart_dict:
                # del cart_dict[sku_id]
                cart_dict.pop(sku_id)
            # 2.3 新的cookie购物车字典写入cookie中
            cart_str = carts_cookie_encode(cart_dict)
            response = JsonResponse({'code': 0, 'errmsg': 'ok'})
            response.set_cookie('carts', cart_str)
            return response

    # 修改购物车
    def put(self, request):
        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')
        count = data.get('count')
        selected = data.get('selected', True)

        user = request.user
        if user.is_authenticated:
            # 登陆，修改redis
            conn = get_redis_connection('carts')
            conn.hmset('carts_%s'%user.id, {sku_id:count}) # 覆盖写入——幂等
            if selected:
                conn.sadd('selected_%s'%user.id, sku_id)
            else:
                conn.srem('selected_%s'%user.id, sku_id)
            return JsonResponse({
                'code': 0,
                'errmsg': 'ok',
                'cart_sku': {
                    'id': sku_id,
                    'count': count,
                    'selected': selected
                }
            })

        else:
            # 未登陆，修改cookie
            # 1、读取cookie购物车
            cart_dict = {}
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = carts_cookie_decode(cart_str)

            # 2、修改cookie购物车
            if not cart_dict:
                return JsonResponse({'code': 0, 'errmsg': 'ok'})

            if sku_id in cart_dict:
                cart_dict[sku_id]['count'] = count # 幂等性
                cart_dict[sku_id]['selected'] = selected

            # 3、新的购物车数据覆写入cookie
            cart_str = carts_cookie_encode(cart_dict)
            # 4、构建响应
            response = JsonResponse({
                'code': 0,
                'errmsg': 'ok',
                'cart_sku': {
                    'id': sku_id,
                    'count': count,
                    'selected': selected
                }
            })
            response.set_cookie(
                'carts',
                cart_str
            )
            return response

    # 展示购物车
    def get(self, request):
        # 0、初始化一个空字典，用于保存sku购物车数据，其格式和cookie购物车格式一样
        cart_dict = {} # {1: {count:xx, selected:xx}}

        user = request.user
        if user.is_authenticated:
            # 1、用户登陆，则从redis中读取sku商品信息
            conn = get_redis_connection('carts')
            # 2、sku商品数量、是否选中
            # cart_redis_dict = {b'1': b'8'}
            cart_redis_dict = conn.hgetall('carts_%s'%user.id)
            # cart_redis_selected = [b'1']
            cart_redis_selected = conn.smembers('selected_%s'%user.id)
            for k, v in cart_redis_dict.items():
                # k: b'1'; v: b'8'
                cart_dict[int(k)] = {
                    'count': int(v),
                    'selected': k in cart_redis_selected # b'1' in [b'1']
                }

        else:
            # 2、用户未登陆，则从cookie中去读sku商品信息
            cart_str = request.COOKIES.get('carts')
            if cart_str:
                cart_dict = carts_cookie_decode(cart_str)

        cart_skus = []
        # 3、构建响应返回
        for k,v in cart_dict.items():
            # k: sku_id; v: {count:xx, selected: xx}
            sku = SKU.objects.get(pk=k)
            cart_skus.append({
                'id': sku.id,
                'name': sku.name,
                'count': v['count'],
                'selected': v['selected'],
                'price': sku.price,
                'default_image_url': sku.default_image_url.url,
                'amount': sku.price * v['count']
            })

        return JsonResponse({'code': 0, 'errmsg': 'ok', 'cart_skus': cart_skus})

    # 把sku商品加入购物车
    def post(self, request):
        # 1、提取参数
        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')
        count = data.get('count')
        selected = data.get('selected', True)

        # 2、校验参数
        if not all([sku_id, count]):
            return JsonResponse({'code': 400, 'errmsg': '缺少参数！'})

        if not isinstance(selected, bool):
            return JsonResponse({'code': 400, 'errmsg': '参数有误！'})

        # 3、判断是否登陆
        user = request.user # 未登陆AnounymousUser对象；已登陆User对象
        if user.is_authenticated:
            # 4、登陆写入redis
            conn = get_redis_connection('carts')
            # 4.1 记录sku商品数量——carts_<user_id> : {sku_id: count}
            # conn.hmset('carts_%s'%user.id, {sku_id:count}) # 我们不能使用该函数，因为他会覆盖原有数据
            conn.hincrby('carts_%s'%user.id, sku_id, amount=count) # 把sku商品数量增加count，如果不存在则新建
            # 4.2 记录选中状态——selected_<user_id> : [sku_id]
            if selected:
                conn.sadd('selected_%s'%user.id, sku_id)

            return JsonResponse({'code': 0, 'errmsg': 'ok'})
        else:
            # 5、未登陆写入cookie
            # 5.1 提取用户cookie购物车数据
            cart_dict = {}
            cart_str = request.COOKIES.get('carts') # ADhjbhjreADSFjkJKBLHJLBfgrewnfgkrbl or None
            if cart_str:
                cart_dict = carts_cookie_decode(cart_str)

            # 5.1 如果本来当前sku就有追加，不再就新建
            if sku_id in cart_dict:
                cart_dict[sku_id]['count'] += count
                cart_dict[sku_id]['selected'] = selected
            else:
                cart_dict[sku_id] = {
                    'count': count,
                    'selected': selected
                }

            # 5.2 重新编码写入cookie
            cart_str = carts_cookie_encode(cart_dict)
            response = JsonResponse({'code': 0, 'errmsg': 'ok'})
            response.set_cookie(
                'carts',
                cart_str
            )
            return response













