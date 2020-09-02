from rest_framework.generics import ListAPIView,CreateAPIView
from meiduo_admin.serializers.user_serializers import *
from meiduo_admin.custom_pagination import MyPage


class UserView(ListAPIView, CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserModelSerializer
    pagination_class = MyPage

    def get_queryset(self):
        #前端传回的查询keyword
        keyword = self.request.query_params.get('keyword')
        if keyword:
            return self.queryset.filter(
                username__contains=keyword,
                is_staff=True
            )
        else:
            return self.queryset.filter(is_staff=True)
