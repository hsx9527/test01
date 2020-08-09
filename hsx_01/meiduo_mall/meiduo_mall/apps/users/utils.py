from django.contrib.auth.backends import ModelBackend
import re
from .models import User

def get_user_by_account(account):
    '''判断 account 是否是手机号, 返回 user 对象'''
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

 # 这是创建user对象,调用get_user_by_accounth函数
 # 因函数设置可以用手机作为用户名,所以参数username可以是手机名或用户名
        user = get_user_by_account(username)

        # 校验 user 是否存在并校验密码是否正确
        if user and user.check_password(password):
            # 如果user存在, 密码正确, 则返回 user
            return user