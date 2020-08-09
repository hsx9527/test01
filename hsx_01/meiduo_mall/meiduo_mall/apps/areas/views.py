from django.shortcuts import render
from django.views import View
from django.http import JsonResponse
from .models import Area
from django.core.cache import cache

class ProvinceAreasView(View):
    def get(self, request):
        p_list = cache.get('province_list')
        if not p_list:
            provinces = Area.objects.filter(
                parent=None
            )
            p_list = []
            for province in provinces:
                p_list.append({
                    'id': province.id,
                    'name': province.name
                })

            # 读取mysql省数据之后，写入缓存
            # cache模块写入缓存是key-value形式
            cache.set('province_list', p_list, 3600)

        # 3、构建响应返回
        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'province_list': p_list
        })

class SubAreasView(View):

    def get(self, request, pk):
        sub_data = cache.get('sub_area_%s'%pk)

        if not sub_data:
            # 当前pk过滤出的父级行政区对象
            p_area = Area.objects.get(
                pk=pk
            )

            # 当前父级行政区对象关联的多个子级行政区
            subs = Area.objects.filter(
                parent_id=pk
            )

            sub_list = []
            for sub in subs:
                sub_list.append({
                    'id': sub.id,
                    'name': sub.name
                })

            sub_data = {
                    'id': p_area.id,
                    'name': p_area.name,
                    'subs': sub_list
            }

            cache.set('sub_area_%s'%pk, sub_data, 3600)

        return JsonResponse({
            'code': 0,
            'errmsg': 'ok',
            'sub_data': sub_data
        })


