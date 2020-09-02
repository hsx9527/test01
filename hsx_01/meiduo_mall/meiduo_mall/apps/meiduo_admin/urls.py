from django.urls import re_path
from rest_framework_jwt.views import obtain_jwt_token
from rest_framework.routers import SimpleRouter
from meiduo_admin.views.home_views import *
from meiduo_admin.views.user_views import *
from meiduo_admin.views.sku_views import *
from meiduo_admin.views.spu_views import *
from meiduo_admin.views.spec_views import *
from meiduo_admin.views.option_views import *
from meiduo_admin.views.image_views import *
from meiduo_admin.views.order_views import *
from meiduo_admin.views.perm_views import *
from meiduo_admin.views.group_views import *
from meiduo_admin.views.admin_views import *



urlpatterns = [
    # obtain_jwt_token: 验证用户名和密码，签发token
    # 默认情况下该视图只会返回token值；
    re_path(r'^authorizations/$', obtain_jwt_token),
    # 统计用户总数
    re_path(r'^statistical/total_count/$', UserTotalCountView.as_view()),
    # 统计当日新建用户数量
    re_path(r'^statistical/day_increment/$', UserDayCountView.as_view()),
    # 日活跃用户数量
    re_path(r'^statistical/day_active/$', UserActiveCountView.as_view()),
    # 日下单用户量
    re_path(r'^statistical/day_orders/$', UserOrderCountView.as_view()),
    # 月增用户统计
    re_path(r'^statistical/month_increment/$', UserMonthCountView.as_view()),
    # 日分类商品访问量
    re_path(r'^statistical/goods_day_views/$', GoodsDayView.as_view()),
    # 用户列表
    re_path(r'^users/$', UserView.as_view()),
    # SKU管理增删改查
    re_path(r'^skus/$', SKUView.as_view({'get': 'list', 'post': 'create'})),
    re_path(r'^skus/(?P<pk>\d+)/$', SKUView.as_view({'get': 'retrieve',
                                                     'put': 'update',
                                                    'delete': 'destroy'
                                                     })),

    # 新增SKU可选三级分类
    re_path(r'^skus/categories/$', SKUCateView.as_view()),
    # 新增SKU可选SPU
    re_path(r'^goods/simple/$', SPUSimpleView.as_view()),
    # 选中的SPU可选的规格和选项
    re_path(r'^goods/(?P<pk>\d+)/specs/$', SpecSimpleView.as_view()),
    # SPU表管理
    re_path(r'^goods/$', SPUView.as_view({'get': 'list', 'post': 'create'})),
    re_path(r'^goods/(?P<pk>\d+)/$', SPUView.as_view({
        'get': 'retrieve',
        'put': 'update',
        'delete': 'destroy'
    })),

    # 可选品牌
    re_path(r'^goods/brands/simple/$', BrandSimpleView.as_view()),
    # 可选一级分类
    re_path(r'^goods/channel/categories/$', GoodsCateSimpleView.as_view()),
    # 可选二级和三级分类
    re_path(r'^goods/channel/categories/(?P<pk>\d+)/$', GoodsCateSimpleView.as_view()),
    # 规格表管理
    re_path(r'^goods/specs/$', SpecView.as_view({'get': 'list', 'post': 'create'})),
    re_path(r'^goods/specs/(?P<pk>\d+)/$', SpecView.as_view({
        'get': 'retrieve', 'put': 'update', 'delete': 'destroy'
    })),
    # 进入新增选项的可选规格
    re_path(r'^goods/specs/simple/$', OptionView.as_view({'get': 'opt_specs'})),
    # 新增图片中可选sku
    re_path(r'^skus/simple/$', SKUSimpleView.as_view()),
    # 订单列表数据
    re_path(r'^orders/$', OrderView.as_view({'get': 'list'})),
    re_path(r'^orders/(?P<pk>\d+)/$', OrderView.as_view({'get': 'retrieve'})),
    re_path(r'^orders/(?P<pk>\d+)/status/$', OrderView.as_view({'patch': 'partial_update'})),#'partial_update'部分更新
    # 权限管理
    re_path(r'^permission/perms/$', PermView.as_view({'get': 'list', 'post':'create'})),
    re_path(r'^permission/perms/(?P<pk>\d+)/$', PermView.as_view({
        'get':'retrieve',
        'put':'update',
        'delete':'destroy'
    })),
    # 权限管理之新增权限可选类型
    re_path(r'^permission/content_types/$', PermContentTypeView.as_view()),
    # 用户组管理
    re_path(r'^permission/groups/$', GroupView.as_view({'get': 'list', 'post': 'create'})),
    re_path(r'^permission/groups/(?P<pk>\d+)/$', GroupView.as_view({
        'get': 'retrieve',
        'put': 'update',
        'delete': 'destroy'
    })),
    # 用户组管理之新增分组可选权限列表
    re_path(r'^permission/simple/$', GroupPermSimpleView.as_view()),
    # ======================================================================================
    # 管理员管理
    re_path(r'^permission/admins/$', AdminView.as_view({'get': 'list', 'post': 'create'})),
    re_path(r'^permission/admins/(?P<pk>\d+)/$', AdminView.as_view({
        'get':'retrieve',
        'put':'update',
        'delete':'destroy'
    })),
    # 管理员新增管理员可选分组
    re_path(r'^permission/groups/simple/$', AdminGroupView.as_view()),
]
# 选项表管理
router = SimpleRouter()
router.register(prefix='specs/options', viewset=OptionView, basename='options')
router.register(prefix='skus/images', viewset=ImageView, basename='skus')
urlpatterns += router.urls


# 选项表管理
# urlpatterns = [
    # re_path(r'^specs/options/$', OptionView.as_view({'get':'list', 'post': 'create'})),
    # re_path(r'^specs/options/(?P<pk>\d+)/$', OptionView.as_view({
    #     'get': 'retrieve',
    #     'put': 'update',
    #     'delete': 'destroy'
    # })),]