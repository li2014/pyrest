# -*- coding: utf-8 -*-
# @Time    : 2017/12/15 12:05
# @Author  : Ayan
# @Email   : hbally
# @File    : __init__.py
# @Software: PyCharm

from app import dbhelper


class BaseDao(object):
    '''
    具体业务不可能直接是 retrieve create update delete需要一些控制和限制
    而且response的数据模型,也会根据业务生成不同的样式，不可能完全是表的项名称
    通过继承BaseDao 然后加以控制并返回输出 这样的工作量是否 比直接某一路由下操作数据库来的方便？ 有无必要，未可知？
    '''

    def __init__(self, table):
        self.table = table

    def retrieve(self, params={}, fields=[], session={}):
        return dbhelper.select(self.table, params)

    def create(self, params={}, fields=[], session={}):
        if '_id' in params and len(params) < 2 or '_id' not in params and len(params) < 1:
            return {"code": 301, "err": "The params is error."}
        return dbhelper.insert(self.table, params)

    def update(self, params={}, fields=[], session={}):
        if '_id' not in params or len(params) < 2:
            return {"code": 301, "err": "The params is error."}
        return dbhelper.update(self.table, params)

    def delete(self, params={}, fields=[], session={}):
        if '_id' not in params:
            return {"code": 301, "err": "The params is error."}
        return dbhelper.delete(self.table, params)
