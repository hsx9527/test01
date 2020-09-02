from django.shortcuts import render
from django.views import View
from users.models import User
from django.http import JsonResponse
# =========================
import re
from django import http
from django_redis import get_redis_connection
from django.contrib.auth import login
import json
from django.contrib.auth import login, authenticate
from django.contrib.auth import logout
from meiduo_mall.utils.views import login_required
from django.utils.decorators import method_decorator
from celery_tasks.email.tasks import send_verify_email
from .models import Address
from carts.utils import merge_cart_cookie_to_redis

class UsernameCountView(View):
    def get(self, request, username):
        try:
            count = User.objects.filter(username=username).count()
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'errmsg':'访问数据库失败'})
        return  JsonResponse({'code': 0,
                              'errmsg':'ok',
                              'count':count})


class MobileCountView(View):
    def get(self, request, mobile):
        try:
            count = User.objects.filter(mobile=mobile).count()
        except Exception as e:
            return JsonResponse({'code': 400,
                                 'errmsg': '查询数据库出错'})
        return JsonResponse({'code': 0,
                             'errmsg': 'ok',
                             'count': count})

# ==============================================================
# 用户注册接口定义


class RegisterView(View):

    def post(self, request):

        dict = json.loads(request.body.decode())
        username = dict.get('username')
        password = dict.get('password')
        password2 = dict.get('password2')
        mobile = dict.get('mobile')
        allow = dict.get('allow')
        sms_code_client = dict.get('sms_code')

        # 2.校验(整体)
        if not all([username, password, password2, mobile, allow, sms_code_client]):
            return http.JsonResponse({'code':400,
                                      'errmsg':'缺少必传参数'})

        # 3.username检验
        if not re.match(r'^[a-zA-Z0-9_-]{5,20}$', username):
            return http.JsonResponse({'code': 400,
                                      'errmsg': 'username格式有误'})

        # 4.password检验
        if not re.match(r'^[a-zA-Z0-9]{8,20}$', password):
            return http.JsonResponse({'code': 400,
                                      'errmsg': 'password格式有误'})

        # 5.password2 和 password
        if password != password2:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '两次输入不对'})
        # 6.mobile检验
        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return http.JsonResponse({'code': 400,
                                      'errmsg': 'mobile格式有误'})
        # 7.allow检验
        if allow != True:
            return http.JsonResponse({'code': 400,
                                      'errmsg': 'allow格式有误'})

        # 8.sms_code检验 (链接redis数据库)
        redis_conn = get_redis_connection('sms_code')

        # 9.从redis中取值
        sms_code_server = redis_conn.get('sms_%s' % mobile)
        print(sms_code_server)

        # 10.判断该值是否存在
        if not sms_code_server:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '短信验证码过期'})
        # 11.把redis中取得值和前端发的值对比
        if sms_code_client != sms_code_server.decode():
            return http.JsonResponse({'code': 400,
                                      'errmsg': '验证码有误'})

        # 保存到数据库
        try:
            user =  User.objects.create_user(username=username,
                                             password=password,
                                             mobile=mobile)
        except Exception as e:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '保存到数据库出错'})

        login(request, user)


        return http.JsonResponse({'code': 0,
                                 'errmsg': 'ok'})


# ==============================================
# 用户名登录后端逻辑
class LoginView(View):

    def post(self, request):
        '''实现登录接口'''
        # 1.接收参数
        dict = json.loads(request.body.decode())
        username = dict.get('username')
        password = dict.get('password')
        remembered = dict.get('remembered')


        # 2.校验(整体 + 单个)
        if not all([username, password]):
            return JsonResponse({'code': 400,
                                 'errmsg': '缺少必传参数'})

        # 3.验证是否能够登录
        user = authenticate(request,username=username,
                            password=password)

        # 判断是否为空,如果为空,返回
        if user is None:
            return JsonResponse({'code': 400,
                                 'errmsg': '用户名或者密码错误'})

        # 4.状态保持
        login(request, user)

        # 5.判断是否记住用户
        if remembered != True:
            # 7.如果没有记住: 关闭立刻失效
            request.session.set_expiry(0)
        else:
            # 6.如果记住:  设置为两周有效
            request.session.set_expiry(None)

        # 8.返回json
        response = JsonResponse({'code': 0,
                             'errmsg': 'ok'})
        # 设置cookie
        response.set_cookie('username', username,max_age=3600*24*14)
        # 登陆成功，返回响应之前，合并购物车
        response = merge_cart_cookie_to_redis(request, user, response)
        return response


# 退出登录
class LogoutView(View):
    """定义退出登录的接口"""

    def delete(self, request):
        """实现退出登录逻辑"""

        # 清理 session
        logout(request)

        # 创建 response 对象.
        response = JsonResponse({'code':0,
                                 'errmsg':'ok'})

        # 调用对象的 delete_cookie 方法, 清除cookie
        response.delete_cookie('username')

        # 返回响应
        return response

# ======================
# 用户接口实现
class UserInfoView(View):

    @method_decorator(login_required)
    def get(self, request):
        user = request.user

        # 2、构造响应数据返回
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'info_data': {
                'username': user.username,
                'mobile': user.mobile,
                'email': user.email,
                'email_active': user.email_active
            }
        })


# =============================
# 更新邮箱接口
class EmailView(View):

    @method_decorator(login_required)
    def put(self, request):
        # 1、提取参数
        data = json.loads(request.body.decode())
        email = data.get('email')
        # 2、校验参数
        if not email:
            return JsonResponse({'code': 400, 'errmsg': '缺少email'})

        if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
            return JsonResponse({'code': 400, 'errmsg': '邮箱格式有误！'})

        # 3、数据处理(部分更新) ———— 更新邮箱
        user = request.user
        try:
            user.email = email
            user.email_active = False
            user.save()
        except Exception as e:
            print(e)


        # ======发送邮箱验证邮件=======
        verify_url = user.generate_verify_email_url()
        send_verify_email.delay(email, verify_url) # 异步调用！

        # 4、构建响应
        return JsonResponse({'code': 0, 'errmsg': 'ok'})



# 确认邮箱接口
class VerifyEmailView(View):

    def put(self, request):
        # 1、提取查询字符串中token
        token = request.GET.get('token')
        # 2、校验token
        user = User.check_verify_email_token(token)
        if not user:
            return JsonResponse({'code': 400, 'errmsg': '验证邮件无效！'})

        # 3、如果token有效，把邮箱的激活状态设置为True
        user.email_active = True
        user.save()

        return JsonResponse({'code': 0, 'errmsg': '邮箱激活成功！'})



# 创建地址接口
class CreateAddressView(View):

    def post(self, request):
        # 1、提取参数
        data = json.loads(request.body.decode())
        receiver = data.get('receiver')
        province_id = data.get('province_id')
        city_id = data.get('city_id')
        district_id = data.get('district_id')
        place = data.get('place') # 详细地址
        mobile = data.get('mobile')
        tel = data.get('tel')
        email = data.get('email')

        # 判断用户地址数量是否超过20个
        user = request.user
        count = Address.objects.filter(user=user).count()
        if count >= 20:
            return JsonResponse({'code': 400, 'errmsg': '数量超限'})


        # 2、校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({"code": 400, 'errmsg': '缺少参数！'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'errmsg': '参数mobile有误'})
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数email有误'})

        # 3、新建用户地址
        try:
            address = Address.objects.create(
                user=user,
                province_id=province_id,
                city_id=city_id,
                district_id=district_id,
                title=receiver, # 当前地址的标题，默认收货人名称就作为地址标题
                receiver=receiver,
                place=place,
                mobile=mobile,
                tel=tel
            )

            # 如果当前新增地址的时候，用户没有设置默认地址，那么
            # 我们把当前新增的地址设置为用户的默认地址
            if not user.default_address:
                user.default_address = address
                user.save()

        except Exception as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '新增地址失败！'})

        address_info = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,

            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,

            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        # 4、返回响应
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'address': address_info
        })


# 地址在网页中展示
class AddressView(View):

    def get(self, request):
        # 1、根据用户，过滤出当前用户的所有地址
        user = request.user
        addresses = Address.objects.filter(
            user=user,
            is_deleted=False # 没有逻辑删除的地址
        )

        # 2、把地址转化成字典
        address_list = []
        for address in addresses:
            if address.id != user.default_address_id:
                address_list.append({
                    'id': address.id,
                    'title': address.title,
                    'receiver': address.receiver,
                    'province': address.province.name,
                    'city': address.city.name,
                    'district': address.district.name,
                    'place': address.place,
                    'mobile': address.mobile,
                    'tel': address.tel,
                    'email': address.email
                })
            else:
                address_list.insert(0, {
                    'id': address.id,
                    'title': address.title,
                    'receiver': address.receiver,
                    'province': address.province.name,
                    'city': address.city.name,
                    'district': address.district.name,
                    'place': address.place,
                    'mobile': address.mobile,
                    'tel': address.tel,
                    'email': address.email
                })

        # 3、构建响应返回
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'default_address_id': user.default_address_id,
            'addresses': address_list
        })

# 总结：相同的请求路径+不同的请求方法 = 统一类视图中
class UpdateDestroyAddressView(View):

    # 删除地址
    def delete(self, request, address_id):
        # 1、根据路径中的地址主键，获取地址对象
        try:
            address = Address.objects.get(pk=address_id)
        except Address.DoesNotExist as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '地址不存在'}, status=404)

        # 2、通过对象删除(真删除，逻辑删除)
        # 真删除: address.delete()
        # 逻辑删除
        address.is_deleted = True
        address.save()

        # 3、构建响应
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok'
        })


    # 更新地址接口
    def put(self, request, address_id):

        # 1、获取被更新的地址
        try:
            address = Address.objects.get(pk=address_id)
        except Address.DoesNotExist as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '资源未找到！'})

        # 2、提取参数
        data = json.loads(request.body.decode())
        receiver = data.get('receiver')
        province_id = data.get('province_id')
        city_id = data.get('city_id')
        district_id = data.get('district_id')
        place = data.get('place')  # 详细地址
        mobile = data.get('mobile')
        tel = data.get('tel')
        email = data.get('email')

        # 3、校验参数
        if not all([receiver, province_id, city_id, district_id, place, mobile]):
            return JsonResponse({"code": 400, 'errmsg': '缺少参数！'})

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return JsonResponse({'code': 400,
                                 'errmsg': '参数mobile有误'})
        if tel:
            if not re.match(r'^(0[0-9]{2,3}-)?([2-9][0-9]{6,7})+(-[0-9]{1,4})?$', tel):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数tel有误'})
        if email:
            if not re.match(r'^[a-z0-9][\w\.\-]*@[a-z0-9\-]+(\.[a-z]{2,5}){1,2}$', email):
                return JsonResponse({'code': 400,
                                     'errmsg': '参数email有误'})


        address.receiver = receiver
        address.province_id = province_id
        address.city_id = city_id
        address.district_id = district_id
        address.place = place
        address.mobile = mobile
        address.tel = tel
        address.email = email
        address.save()#保存,事务结束

        # data = {"receiver": "韦小宝宝"}
        # update(**data) -->  update(receiver="韦小宝宝")
        # data.pop('province')
        # data.pop('city')
        # data.pop('district')
        # Address.objects.filter(pk=address_id).update(**data)
        # address = Address.objects.get(pk=address_id)

        address_info = {
            "id": address.id,
            "title": address.title,
            "receiver": address.receiver,

            "province": address.province.name,
            "city": address.city.name,
            "district": address.district.name,

            "place": address.place,
            "mobile": address.mobile,
            "tel": address.tel,
            "email": address.email
        }

        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'address': address_info
        })

# 设置默认地址
class DefaultAddressView(View):

    def put(self, request, address_id):
        # 修改当前登陆用户对象的default_address指向address_id的地址
        user = request.user

        # default_address是ForeignKey类型，是Address对象
        # user.default_address = <Address对象>
        # user.default_address = Address.objects.get(pk=address_id)

        # user.default_address_id = <Address对象的主键>
        user.default_address_id = address_id

        user.save()

        return JsonResponse({
            'code': 0,
            'errmsg': 'ok'
        })


# 修改地址标题
class UpdateTitleAddressView(View):

    def put(self, request, address_id):
        # 1、获取更新数据
        data = json.loads(request.body.decode())
        title = data.get('title')

        # 2、获取被修改的地址对象
        address = Address.objects.get(pk=address_id)

        # 3、修改并返回响应
        address.title = title
        address.save()

        return JsonResponse({'code': 0, 'errmsg': 'ok'})


# 修改用户密码
class ChangePasswordView(View):

    def put(self, request):
        data = json.loads(request.body.decode())
        old_password = data.get('old_password')
        new_password = data.get('new_password')
        new_password2 = data.get('new_password2')
        if not all([old_password, new_password, new_password2]):
            return JsonResponse({'code':400, 'errmsg': '参数缺失'})
        if not re.match(r'^[0-9A-Za-z]{8,20}$', new_password):
            return JsonResponse({'code': 400,
                             'errmsg': '密码最少8位,最长20位'})
        if new_password != new_password2:
            return JsonResponse({'code': 400,
                             'errmsg': '两次输入密码不一致'})
        user = request.user
        if not user.check_password(old_password):
            return JsonResponse({'code': 400, 'errmsg': '旧密码有误！'}, status=400)
        # 更新密码
        user.set_password(new_password)
        # 声明事务结束
        user.save()
        # 因mysql具有隔离性,python感知不到,重新调用
        logout(request)

        response = JsonResponse({'code': 0, 'errmsg': 'ok'})
        response.delete_cookie('username')
        return response


# 用户浏览商品记录
from django.utils import timezone
from goods.models import SKU,GoodsVisitCount
class UserBrowseHistory(View):

    @method_decorator(login_required)
    def post(self, request):
        # 记录用户历史
        # 1、获取请求参数
        data = json.loads(request.body.decode())
        sku_id = data.get('sku_id')

        user = request.user
        # 2、加入用户历史记录redis列表中
        conn = get_redis_connection('history')
        p = conn.pipeline()
        # 2.1 去重
        p.lrem('history_%s'%user.id, 0, sku_id)
        # 2.2 左侧插入
        p.lpush('history_%s'%user.id, sku_id)
        # 2.3 截断列表(保证最多5条)
        p.ltrim('history_%s'%user.id, 0, 4)
        p.execute()

        # 补充：当前用户访问的sku的类别商品访问量累加
        sku = SKU.objects.get(pk=sku_id)
        category = sku.category
        try:
            good_visit = GoodsVisitCount.objects.get(
                category_id=category.id,
                create_time__gte=timezone.localtime().replace(hour=0, minute=0, second=0)
            )
        except GoodsVisitCount.DoesNotExist as e:
            # 当日该类别历史记录不存在
            GoodsVisitCount.objects.create(
                count=1,
                category=category,
            )
        else:
            good_visit.count += 1
            good_visit.save()

        # 3、构建响应
        return JsonResponse({'code': 0, 'errmsg': 'ok'})


    @method_decorator(login_required)
    def get(self, request):
        # 展示用户浏览历史
        user = request.user

        conn = get_redis_connection('history')
        # 1、读取redis浏览历史
        # sku_ids = [b'4', b'5', b'11']
        sku_ids = conn.lrange('history_%s'%user.id, 0, -1)
        # 2、获取sku商品信息
        # sku_ids = [int(x) for x in sku_ids]
        skus = SKU.objects.filter(id__in=sku_ids)
        # 3、构建响应
        sku_list = []
        for sku in skus:
            sku_list.append({
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image_url.url
            })
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'skus': sku_list
        })