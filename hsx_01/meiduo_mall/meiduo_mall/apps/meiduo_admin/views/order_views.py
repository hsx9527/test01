from rest_framework.viewsets import ModelViewSet
from meiduo_admin.serializers.order_serializers import *
from meiduo_admin.custom_pagination import MyPage

# 订单管理
class OrderView(ModelViewSet):
    queryset = OrderInfo.objects.all()
    serializer_class = OrderSimpleModelSerializer
    pagination_class = MyPage

    def get_queryset(self):
        keyword = self.request.query_params.get('keyword')
        if keyword:
            return self.queryset.filter(order_id__contains=keyword)
        return self.queryset.all()

    # 如何在同一个视图的不同接口中使用不同的序列化器实现不同的序列化/反序列化操作!
    def get_serializer_class(self):
        # self.action:是当前请求处理的视图函数的名称
        if self.action == 'list':
            return self.serializer_class
        elif self.action == 'retrieve':
            return OrderDetailModelSerializer
        elif self.action == 'partial_update':
            return OrderDetailModelSerializer