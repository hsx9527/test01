from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from users.models import User
from rest_framework.permissions import IsAdminUser


# 所有用户
class UserTotalCountView(APIView):

    permission_classes = [IsAdminUser]

    def get(self, request):
        # 1、统计出用户数量
        count = User.objects.count()
        # 根据Django配置中的TIME_ZONE来获取指定时区的当前时刻
        cur_time = timezone.localtime()
        # 2、构建响应
        return Response({
            'count': count,
            # 'date': <当日> —— 本地当前
            'date': cur_time.date()
        })


# 当天新增用户
class UserDayCountView(APIView):
    #简单说就是管理者才能执行以下内容
    permission_classes = [IsAdminUser]
    def get(self, request):
        cur_time = timezone.localtime()
        #cur_time.零时
        cur_0_time = cur_time.replace(hour=0, minute=0, second=0)
        #date_joined__gte:这里是大于0时刻的数据对象进行计算
        # date_joined记录新创用户的新创时间
        count = User.objects.filter(
            date_joined__gte=cur_0_time
        ).count()

        return Response({
            'count': count,
            'date': cur_time.date()
        })


# 日活量
class UserActiveCountView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        cur_0_time = timezone.localtime().replace(
            hour=0, minute=0, second=0
        )
        #last_login记录最后登录的时间
        count = User.objects.filter(
            last_login__gte=cur_0_time
        ).count()
        return Response({
            'count': count,
            'date': cur_0_time.date()
        })

# 订单
from orders.models import OrderInfo
class UserOrderCountView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        cur_0_time = timezone.localtime().replace(
            hour=0, minute=0, second=0
        )

        # orders = OrderInfo.objects.filter(
        #     create_time__gte=cur_0_time
        # )
        # ===============================
        # user_set = set() # 自动去重
        # 关联主表
        # for order in orders:
        #     user_set.add(order.user)
            #去重
        # count = len(user_set)
        # =============================
        # 在内置OrderInfo对象中主表User外键user中添加related_name='orders',
        order_users = User.objects.filter(
            # orders代表从表中的外键主表中一个关联属性,直接使用
            orders__create_time__gte=cur_0_time
        ) # 没有去重
        count = len(set(order_users))
        # ==========================================
        return Response({
            'count': count,
            'date': cur_0_time.date()#返回本地当前查询日期
        })


# 月增
from datetime import timedelta
class UserMonthCountView(APIView):
    permission_classes = [IsAdminUser]
    def get(self, request):
        cur_0_time = timezone.localtime().replace(
            hour=0, minute=0, second=0
        )
        #最后一天的0时刻
        end_0_time = cur_0_time
        #开始的0时刻
        start_0_time = end_0_time - timedelta(days=29)
        ret_list = []
        for index in range(30):
            # 从30天前开始计算
            calc_0_time = start_0_time + timedelta(days=index)
            count = User.objects.filter(
                date_joined__gte=calc_0_time, # 大于等于当日0时刻
                date_joined__lt=calc_0_time + timedelta(days=1) # 小于次日0时刻
            ).count()

            ret_list.append({
                'count': count,
                'date': calc_0_time.date()
            })
        return Response(ret_list)

# 日商品分类访问
from rest_framework.generics import ListAPIView
from meiduo_admin.serializers.home_serializers import *
class GoodsDayView(ListAPIView):
    queryset = GoodsVisitCount.objects.all()
    serializer_class = GoodVistiModelSerializer
    def get_queryset(self):
        cur_0_time = timezone.localtime().replace(
            hour=0, minute=0, second=0
        )
        return GoodsVisitCount.objects.filter(
            create_time__gte=cur_0_time
        )