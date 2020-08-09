from haystack import indexes
from .models import SKU
# 针对ES搜索引擎库定义一个索引模型类
class SKUIndex(indexes.SearchIndex, indexes.Indexable):
   # 用户与es交互的接口
    text = indexes.CharField(document=True, use_template=True)
    def get_model(self):
        # 获取被检索数据的模型类
        return SKU
    def index_queryset(self, using=None):
        return self.get_model().objects.filter(is_launched=True)