from django_redis import get_redis_connection
import pickle,base64


# Cookie数据的编码
def carts_cookie_encode(cart_dict):
    # 1、使用pickle把字段编码成字节
    # 2、base64编码把字节编程成可视化字符
    return base64.b64encode(
        pickle.dumps(cart_dict)
    ).decode()


# Cookie数据解码
def carts_cookie_decode(cart_str):
    # 1、base解码
    # 2、pickle解码
    return pickle.loads(
        base64.b64decode(cart_str.encode())
    )


# 合并购物车数据
def merge_cart_cookie_to_redis(request, user, response):
    # 1、读取cookie购物车数据
    cart_dict = {} # 初始化孔子点，保存cookie购物数据
    cookie_str = request.COOKIES.get('carts')
    if cookie_str:
        cart_dict = carts_cookie_decode(cookie_str)
    new_add = cart_dict.keys()
    # (3)、操作redis购物车
    conn = get_redis_connection('carts')
    for sku_id in new_add:
        # 覆盖写入
        conn.hmset('carts_%s'%user.id, {sku_id:cart_dict[sku_id]['count']})
        # cookie中所有已经选中到商品sku_id加入redis集合，未选中的sku_id从redis集合中删除
        if cart_dict[sku_id]['selected']:
            conn.sadd('selected_%s'%user.id, sku_id)
        else:
            conn.srem('selected_%s'%user.id, sku_id)

    # 3、删除cookie购物车
    response.delete_cookie('carts')
    return response