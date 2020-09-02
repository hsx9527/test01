from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from django.core.paginator import Paginator,EmptyPage
from .models import SKU,GoodsCategory
from .utils import get_breadcrumb
# from haystack.views import SearchView
# Create your views here.


# sku商品列表数据返回（分页）
class ListView(View):

    def get(self, request, category_id):

        page = request.GET.get('page')
        page_size = request.GET.get('page_size')
        ordering = request.GET.get('ordering') # -create_time

        # 1、获取sku商品数据 —— 排序
        skus = SKU.objects.filter(
            category_id=category_id,
            is_launched=True # 商品是上架状态
        ).order_by(ordering) # order_by('-create_time')


        # 2、分页 —— 根据page和page_size分页
        # 使用django的接口对一个模型类查询集分页
        # 实例化一个分页器对象，传入skus被分页对目标数据(查询集)，传入page_size来指定按照每页几个划分
        paginator = Paginator(skus, page_size)
        print("数据总量：", paginator.count)
        print("总页数：", paginator.num_pages)

        try:
            # 分页器对象.page函数调用传入page标示获取第几页
            # 返回值是一个查询集，表示当前页数据查询集
            cur_page = paginator.page(page)
        except EmptyPage as e:
            print(e)
            return JsonResponse({'code': 400, 'errmsg': '空页！'})

        ret_list = []
        for sku in cur_page:
            ret_list.append({
                'id': sku.id,
                'default_image_url': sku.default_image_url.url,
                'name': sku.name,
                'price': sku.price
            })

        breadcrumb = get_breadcrumb(category_id)

        # 3、构建响应返回
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'breadcrumb': breadcrumb,
            'list': ret_list,
            'count': paginator.num_pages # 总页数
        })


# 热销商品
class HotGoodsView(View):

    def get(self, request, category_id):
        # 1、获取热销商品(取销量最高的2个)
        skus = SKU.objects.filter(
            category_id=category_id,
            is_launched=True
        ).order_by('-sales')[:2] # 根据销量降序排列

        # 2、构建响应返回
        ret_list = []
        for sku in skus:
            ret_list.append({
                'id': sku.id,
                'name': sku.name,
                'price': sku.price,
                'default_image_url': sku.default_image_url.url
            })

        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'hot_skus': ret_list
        })
    
# 搜索
# class MySearchView(SearchView):
#     def create_response(self):
#         context = self.get_context()
#         sku_list = []
#         for search_result in context['page'].object_list:
#             sku = search_result.object
#             sku_list.append({
#                 'id': sku.id,
#                 'name': sku.name,
#                 'price': sku.price,
#                 'default_image_url': sku.default_image_url.url,
#                 'searchkey': context['query'],
#                 'page_size': context['paginator'].per_page,
#                 'count': context['paginator'].count
#             })
#
#         return JsonResponse(sku_list, safe=False)