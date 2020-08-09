from django.shortcuts import render

# Create your views here.
from django.views import View
from django.http import HttpResponse
from django_redis import get_redis_connection
from meiduo_mall.libs.captcha.captcha import captcha
# ==============================================
import logging
logger = logging.getLogger('django')
import random
from django import http
from meiduo_mall.libs.yuntongxun.ccp_sms import CCP
from celery_tasks.sms.tasks import ccp_send_sms_code

class ImageCodeView(View):
    '''返回图形验证码的类视图'''

    def get(self, request, uuid):

        # 1.调用工具类 captcha 生成图形验证码
        text, image = captcha.generate_captcha()

        # 2.链接 redis, 获取链接对象
        redis_conn = get_redis_connection('verify_code')

        # 3.利用链接对象, 保存数据到 redis, 使用 setex 函数
        # redis_conn.setex('<key>', '<expire>', '<value>')
        redis_conn.setex('img_%s' % uuid, 300, text)

        # 4.返回(图片)
        return HttpResponse(image,
                            content_type='image/jpg')

# =======================================================

class SMSCodeView(View):
    """短信验证码"""

    def get(self, reqeust, mobile):
        redis_conn = get_redis_connection('sms_code')
        send_flag = redis_conn.get('send_flag_%s' % mobile)
        if send_flag:
            return http.JsonResponse({'code': 400,
                                      'errmsg': '发送短信过于频繁'})

        # 1. 接收参数
        image_code_client = reqeust.GET.get('image_code')
        uuid = reqeust.GET.get('image_code_id')

        # 2. 校验参数
        if not all([image_code_client, uuid]):
            return http.JsonResponse({'code': 400,
                                      'errmsg': '缺少必传参数'})

        # 3. 创建连接到redis的对象
        redis_conn = get_redis_connection('verify_code')

        # 4. 提取图形验证码
        image_code_server = redis_conn.get('img_%s' % uuid)
        if image_code_server is None:
            # 图形验证码过期或者不存在
            return http.JsonResponse({'code': 400,
                                      'errmsg': '图形验证码失效'})


        try:
            redis_conn.delete('img_%s' % uuid)
        except Exception as e:
            logger.error(e)

        # 6. 对比图形验证码
        # bytes 转字符串
        image_code_server = image_code_server.decode()
        # 转小写后比较
        if image_code_client.lower() != image_code_server.lower():
            return http.JsonResponse({'code': 400,
                                      'errmsg': '输入图形验证码有误'})
# =============================================================================
        redis_conn = get_redis_connection('sms_code')
        # 7. 生成短信验证码：生成6位数验证码
        sms_code = '%06d' % random.randint(0, 999999)
        logger.info(sms_code)
        # print('手机验证码:' ,sms_code)

        pl = redis_conn.pipeline()
        # 8. 保存短信验证码
        # 短信验证码有效期，单位：300秒
        pl.setex('sms_%s' % mobile,
                         300,
                         sms_code)
        # 标志位
        pl.setex('send_flag_%s' % mobile, 60, 1)

        pl.execute()
        # 9. 发送短信验证码
        # 短信模板
        # CCP().send_template_sms(mobile,[sms_code, 5], 1)
        ccp_send_sms_code.delay(mobile, sms_code)
        # 10. 响应结果
        return http.JsonResponse({'code': 0,
                                  'errmsg': '发送短信成功'})