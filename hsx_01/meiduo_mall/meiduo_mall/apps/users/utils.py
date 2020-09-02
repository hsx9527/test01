from django.contrib.auth.backends import ModelBackend
import re
from .models import User
from django.utils import timezone

# 封装判断手机登录或用户登录
def get_user_by_account(account):
    try:
        if re.match('^1[3-9]\d{9}$', account):
            user = User.objects.get(mobile=account)
        else:
            user = User.objects.get(username=account)
    except Exception as e:
        return None
    else:
        return user

# 继承自 ModelBackend, 重写 authenticate 函数
class UsernameMobileAuthBackend(ModelBackend):
    """自定义用户认证后端"""
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = get_user_by_account(username)

        # 管理站请求管理站的请求(None)
        if request is None:
            if not user.is_staff:
                return None

        # 校验 user 是否存在并校验密码是否正确
        if user and user.check_password(password):
            # timezone.localtime()获取当前时刻,并没有用到内置函数last_login
            user.last_login = timezone.localtime()  # 记录用户最新登陆的时间
            user.save()
            # 如果user存在, 密码正确, 则返回 user
            return user



 # 后台管理登录参数重构
def my_jwt_response_payload_handler(token, user=None, request=None):
    return {
        'username': user.username,
        'user_id': user.id,
        'token': token
    }