from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response

class MyPage(PageNumberPagination):
    # 约定查询字符串参数: ?page=1&pagesize=5
    page_query_param = 'page'
    page_size_query_param = "pagesize"
    # 约定默认值
    page_size = 5
    # 每页最大数
    max_page_size = 10

    # 默认分页器构造的分页返回结果不符合接口需求
    # 所以需要重写函数，实现自定义分页结果
    def get_paginated_response(self, data):
        # data: 过滤的子集序列化的结果(当前页列表嵌套字典数据)
        return Response({
            'counts': self.page.paginator.count,
            'lists': data,
            'page': self.page.number,
            'pages': self.page.paginator.num_pages,
            'pagesize': self.page_size
        })