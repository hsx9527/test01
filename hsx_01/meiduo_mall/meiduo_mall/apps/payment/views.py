from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.conf import settings
from orders.models import OrderInfo
from .models import Payment
from alipay import AliPay
import os


# 支付状态
class PaymentStatusView(View):

    def put(self, request):
        # 用户支付成功之后，跳转回美多页面的请求
        # 校验是否支付成功

        # 1、提取查询字符串参数
        data = request.GET # QueryDict类型
        data = data.dict() # QueryDict.dict()转化成普通字典
        # 提取签名(token值)
        sign = data.pop('sign')

        # 2、根据签名验证数据是否完整
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            # 异步回调，支付成功之后，阿里后台主动请求美多
            app_notify_url=None,
            # 美多私钥
            app_private_key_path=os.path.join(
                os.path.dirname(
                    os.path.abspath(__file__)
                ), 'keys/app_private_key.pem'),
            # 阿里公钥
            alipay_public_key_path=os.path.join(
                os.path.dirname(
                    os.path.abspath(__file__)
                ), 'keys/alipay_public_key.pem'),
            sign_type='RSA2',
            debug=settings.ALIPAY_DEBUG
        )
        if not alipay.verify(
            data,
            signature=sign
        ):
            return JsonResponse({'code': 400, 'errmsg': '支付失败！'}, status=400)

        # 3、美多订单号和支付宝流水号关联
        order_id = data.get('out_trade_no')
        trade_id = data.get('trade_no')

        try:
            Payment.objects.create(
                order_id=order_id,
                trade_id=trade_id,
            )
        except Exception as e:
            print(e)
            return JsonResponse({
                'code': 400,
                'errmsg': '支付订单保存失败！'
            })

        # 修改订单状态
        OrderInfo.objects.filter(
            order_id=order_id
        ).update(
            status=OrderInfo.ORDER_STATUS_ENUM['UNSEND']
        )

        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'trade_id': trade_id
        })


# 支付接口
class PaymentView(View):

    # 接口1、获取支付页面链接
    def get(self, request, order_id):
        # 1、提取参数
        # 2、校验参数
        try:
            order = OrderInfo.objects.get(pk=order_id)
        except OrderInfo.DoesNotExist as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '订单不存在！'}, status=404)

        # 3、获取支付页面链接
        alipay_url = None

        # 3.1 构建一个Alipay对象
        alipay = AliPay(
            appid=settings.ALIPAY_APPID,
            # 异步回调，支付成功之后，阿里后台主动请求美多
            app_notify_url=None,
            # 美多私钥
            app_private_key_path=os.path.join(
                os.path.dirname(
                    os.path.abspath(__file__)
                ), 'keys/app_private_key.pem'),
            # 阿里公钥
            alipay_public_key_path=os.path.join(
                os.path.dirname(
                    os.path.abspath(__file__)
                ), 'keys/alipay_public_key.pem'),
            sign_type='RSA2',
            debug=settings.ALIPAY_DEBUG
        )

        # 3.2 调用对象的方法
        # 扫码页面完整的链接是：
        # https://openapi.alipaydev.com/gateway.do?<查询字符串参数>
        # order_string = alipay.api_alipay_trade_app_pay() # 移动端
        # 网页端
        order_string = alipay.api_alipay_trade_page_pay(
            subject='美多商城%s'%order_id,
            out_trade_no=order_id,
            total_amount=float(order.total_amount),
            # 支付成功之后，用户页面跳转地址
            return_url=settings.ALIPAY_RETURN_URL
        )

        # 4、构建响应返回
        alipay_url = settings.ALIPAY_URL + '?' + order_string

        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'alipay_url': alipay_url
        })