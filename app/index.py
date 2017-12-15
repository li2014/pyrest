# -*- coding: utf-8 -*-
# @Time    : 2017/12/15 12:05
# @Author  : Ayan
# @Email   : hbally
# @File    : __init__.py
# @Software: PyCharm

import json

from flask import Flask
from flask import request, jsonify
from werkzeug.routing import BaseConverter

from app.baseDao import BaseDao


def check_json_format(raw_msg):
    '''检测body是否为json格式'''
    try:
        js = json.loads(raw_msg, encoding='utf-8')
    except ValueError:
        return False, {}
    return True, js


class RegexConverter(BaseConverter):
    '''让app.route支持路由正则化'''
    def __init__(self, map, *args):
        self.map = map
        self.regex = args[0]


app = Flask(__name__)
#指定路由正则解释器
app.url_map.converters['regex'] = RegexConverter


@app.route('/rs/<regex(".*"):query_url>', methods=['PUT', 'DELETE', 'POST', 'GET'])
def usual_query_method(query_url):
    '''格式规定如下：
        [GET]/rs/users/{id}
        [GET]/rs/users/key1/value1/key2/value2/.../keyn/valuen
        [POST]/rs/users
        [PUT]/rs/users/{id}
        [DELETE]/rs/users/{id}
        按照下面解析按照上面规则进行
    '''
    #映射baseDao中的方法即CURD操作create,update,retrieve,delete
    method = {
        "GET": "retrieve",
        "POST": "create",
        "PUT": "update",
        "DELETE": "delete"
    }
    (flag, params) = check_json_format(request.data)

    urls = query_url.split('/')
    url_len = len(urls)
    ps = {}
    if url_len > 0:
        table = urls[0]
    if url_len == 1 and (request.method == 'POST' or request.method == 'GET'):
        pass
    elif url_len == 2:
        ps['_id'] = urls[1]
    elif url_len > 2 and (request.method == 'GET' or request.method == 'DELETE') and url_len % 2 == 1:
        for i, al in enumerate(urls):#enumerate同时获得索引和值
            if i == 0:
                continue
            if i % 2 == 1:
                tmp = al
            else:
                ps[tmp] = al
    else:
        return "The rest api is not exist."

    if (request.method == 'POST' or request.method == 'PUT') and ps.get('_id'):
        params = dict(params, **{'_id': ps.get('_id')})
    if request.method == 'GET' or request.method == 'DELETE':
        params = ps
    #调用basedao中的curd方法
    rs = getattr(BaseDao(table), method[request.method])(params, [], {})
    return jsonify(rs)


if __name__=="__main__":
    '''
    POST http://127.0.0.1:5000/rs/users
    {
      "name":"xxxx",
      "phone":"13247102983",
      "address":"深圳华强深圳华强北110011",
      "status":1
    }
    
    '''
    app.run()
