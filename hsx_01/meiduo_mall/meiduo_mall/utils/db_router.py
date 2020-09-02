"""
定义mysql数据库路由
"""

class MasterSlaveDBRouter(object):

    # 1、指定读操作的数据库配置
    def db_for_read(self, model, **hints):
        # model：模型类
        return 'slave'

    # 2、指定写操作的数据库配置
    def db_for_write(self, model, **hints):
        return 'default'

    def allow_relation(self, obj1, obj2, **hints):
        # 表示允许关联操作
        return True