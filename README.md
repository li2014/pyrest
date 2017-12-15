一直在用node.js做后端，要逐步涉猎大数据范围，注定绕不过python，因此决定把一些成熟的东西用python来重写，一是开拓思路、通过比较来深入学习python；二是有目标，有动力，希望能持之以恒的坚持下去。

### 项目介绍
用python语言来写一个restful api service，数据库使用mysql。因为只做后端微服务，并且ORM的实现方式，采用自动生成SQL的方式来完成，因此选择了轻量级的flask作为web框架。如此选择，主要目的是针对中小规模的网络应用，能充分利用关系数据库的种种优势，来实现丰富的现代互联网应用。

### restful api
restful api 的概念就不介绍了。这里说一下我们实现协议形式：


```
[GET]/rs/user/{id}/key1/value1/key2/value2/.../keyn/valuen
[POST]/rs/user[/{id}]
[PUT]/rs/user/{id}
[DELETE]/rs/user/{id}/key1/value1/key2/value2/.../keyn/valuen
```

##### 说明：
- rs为资源标识；
- 第二节，user，会被解析为数据库表名；
- 查询时，id为空或0时，id会被忽略，即为列表查询；
- 新建和修改，除接收form表单外，url中的id参数也会被合并到参数集合中；
- 删除同查询。

###  让flask支持正则表达式
flask默认路由不支持正则表达式，而我需要截取完整的URL自己来解析，经查询，按以下步骤很容易完成任务。
- 使用werkzeug库 ：from werkzeug.routing import BaseConverter
- 定义转换器：

```
class RegexConverter(BaseConverter):
    def __init__(self, map, *args):
        self.map = map
        self.regex = args[0]
```

注册转换器 ：
```
app.url_map.converters['regex'] = RegexConverter
```

用正则来截取url :
```
@app.route('/rs/<regex(".*"):query_url>', methods=['PUT', 'DELETE', 'POST', 'GET'])
```

几点疑问：

正则（.*）理论上应该是匹配任何除回车的所有字符，但不知道为什么，在这里不识别问号（？）
我用request.data来取表单数据，为何request.form取不到？

```
'/rs/<regex("."):query_url>'
```
后若加个反斜杠
```
（'/rs/<regex("."):query_url>/'）
```
，request.data就取不到数据，为什么？
解析json数据
解析json数据很容易，但我需要对客户端送上来的数据进行校验，下面是用异常处理又只解析一次的解决方案。

```
def check_json_format(raw_msg):
    try:
        js = json.loads(raw_msg, encoding='utf-8')
    except ValueError:
        return False, {}
    return True, js
```

URL解析
按既定协议解析URL，提取表名，为生成sql组合参数集合。

```
@app.route('/rs/<regex(".*"):query_url>', methods=['PUT', 'DELETE', 'POST', 'GET'])
def rs(query_url):
    (flag, params) = check_json_format(request.data)

    urls = query_url.split('/')
    url_len = len(urls)
    if url_len < 1 or url_len > 2 and url_len % 2 == 1:
        return "The params is wrong."

    ps = {}
    for i, al in enumerate(urls):
        if i == 0:
            table = al
        elif i == 1:
            idd = al
        elif i > 1 and i % 2 == 0:
            tmp = al
        else:
            ps[tmp] = al

    ps['table'] = table
    if url_len > 1:
        ps['id'] = idd
    if request.method == 'POST' or request.method == 'PUT':
        params = dict(params, **{'table': ps.get('table'), 'id': ps.get('id')})
    if request.method == 'GET' or request.method == 'DELETE':
        params = ps
    return jsonify(params)
```

pycharm项目配置
配置好Run/Debug Configurations才能在IDE中运行并单步调试，可以很熟悉flask框架的运行原理。


```
Script path : /usr/local/bin/flask
Parameters : run
环境变量
FLASK_APP = index.py
LC_ALL = en_US.utf-8
LANG = en_US.utf-8
```

本以为配置完上面三条就能运行了，因为在终端模拟器上就已经能正常运行。结果在IDE中出现了一堆莫名的错误，仔细看，大概是编码配置的问题。经搜索，还需要配置后面两个环境变量才能正常运行，大概原因是python版本2与3之间的区别。

### 小结
今天利用flask完成了web基础架构，能够正确解析URL，提取客户端提交的数据，按请求的不同方式来组合我们需要的数据。




```
今天项目已经能够做一个简单的后端服务了，在mysql中新建一个表，就能自动提供restful api的CURD服务了。
```

### 关键点
- 根据REST的四种动词形式，动态调用相应的CURD方法；
- 编写REST与基础数据库访问类之间的中间层（baseDao），实现从REST到数据访问接口之间能用业务逻辑处理；
- 编写基础数据库访问类（dehelper），实现从字典形式的参数向SQL语句的转换；

### 实现的rest-api

实现了如下形式的rest-api


```
[GET]/rs/users/{id}
[GET]/rs/users/key1/value1/key2/value2/.../keyn/valuen
[POST]/rs/users
[PUT]/rs/users/{id}
[DELETE]/rs/users/{id}
```

### 基础数据库访问类
该类实现与pymysql库的对接，提供标准CURD接口。

### 准备数据库表
在数据库对应建立users表，脚本如下：


```
CREATE TABLE `users` (
  `_id` int(11) NOT NULL AUTO_INCREMENT,
  `name` varchar(32) CHARACTER SET utf8mb4 DEFAULT '' COMMENT '标题名称',
  `phone` varchar(1024) DEFAULT '',
  `address` varchar(1024) DEFAULT NULL,
  `status` tinyint(4) DEFAULT '1' COMMENT '状态：0-禁；1-有效；9删除',
  `create_time` datetime DEFAULT CURRENT_TIMESTAMP COMMENT '创建时间',
  PRIMARY KEY (`_id`),
  UNIQUE KEY `uuid` (`_id`) USING BTREE
) ENGINE=InnoDB AUTO_INCREMENT=1 DEFAULT CHARSET=utf8 COMMENT='表';
```

新建数据库配置文件（configs.json）
数据连接配置，不入版本库。


```
{
  "db_config": {
    "db_host": "ip",
    "db_port": 1234,
    "db_username": "root",
    "db_password": "******",
    "db_database": "name",
    "db_charset": "utf8mb4"
  }
}
```

### 对接pymysql接口
用函数exec_sql封装pymysql，提供统一访问mysql的接口。is_query函数用来区分是查询（R）还是执行（CUD）操作。出错处理折腾了好久，插入异常返回的错误形式与其它的竟然不一样！返回参数是一个三元组（执行是否成功，查询结果或错误对象，查询结果数或受影响的行数）


```
with open("./configs.json", 'r', encoding='utf-8') as json_file:
    dbconf = json.load(json_file)['db_config']


def exec_sql(sql, values, is_query=False):
    try:
        flag = False       #是否有异常
        error = {}         #若异常，保存错误信息
        conn = pymysql.connect(host=dbconf['db_host'], port=dbconf['db_port'], user=dbconf['db_username'],
                               passwd=dbconf['db_password'], db=dbconf['db_database'], charset=dbconf['db_charset'])
        with conn.cursor(pymysql.cursors.DictCursor) as cursor:
            num = cursor.execute(sql, values)       #查询结果集数量或执行影响行数
        if is_query:                                #查询取所有结果
            result = cursor.fetchall()
        else:                                       #执行提交
            conn.commit()
        print('Sql: ', sql, ' Values: ', values)
    except Exception as err:
        flag = True
        error = err
        print('Error: ', err)
    finally:
        conn.close()
        if flag:
            return False, error, num if 'num' in dir() else 0
    return True, result if 'result' in dir() else '', num
```

### 查询接口
pymysql的查询接口，可以接受数组，元组和字典，本查询接口使用数组形式来调用。现在此接口只支持与条件组合参数。


```
def select(tablename, params={}, fields=[]):
    sql = "select %s from %s " % ('*' if len(fields) == 0 else ','.join(fields), tablename)
    ks = params.keys()
    where = ""
    ps = []
    pvs = []
    if len(ks) > 0:                    #存在查询条件时，以与方式组合
        for al in ks:
            ps.append(al + " =%s ")
            pvs.append(params[al])
        where += ' where ' + ' and '.join(ps)

    rs = exec_sql(sql+where, pvs, True)
    print('Result: ', rs)
    if rs[0]:
        return {"code": 200, "rows": rs[1], "total": rs[2]}
    else:
        return {"code": rs[1].args[0], "error": rs[1].args[1], "total": rs[2]}
```

### 插入接口
以数组形式提供参数，错误信息解析与其它接口不同。


```
def insert(tablename, params={}):
    sql = "insert into %s " % tablename
    ks = params.keys()
    sql += "(`" + "`,`".join(ks) + "`)"               #字段组合
    vs = list(params.values())                        #值组合，由元组转换为数组
    sql += " values (%s)" % ','.join(['%s']*len(vs))  #配置相应的占位符
    rs = exec_sql(sql, vs)
    if rs[0]:
        return {"code": 200, "info": "create success.", "total": rs[2]}
    else:
        return {"code": 204, "error": rs[1].args[0], "total": rs[2]}
```

### 修改接口
以字典形式提供参数，占位符的形式为：%（keyname）s，只支持按主键进行修改。


```
def update(tablename, params={}):
    sql = "update %s set " % tablename
    ks = params.keys()
    for al in ks:                                    #字段与占位符拼接
        sql += "`" + al + "` = %(" + al + ")s,"
    sql = sql[:-1]                                   #去掉最后一个逗号
    sql += " where _id = %(_id)s "                   #只支持按主键进行修改
    rs = exec_sql(sql, params)                       #提供字典参数
    if rs[0]:
        return {"code": 200, "info": "update success.", "total": rs[2]}
    else:
        return {"code": rs[1].args[0], "error": rs[1].args[1], "total": rs[2]}
```

### 删除接口
以字典形式提供参数，占位符的形式为：%（keyname）s，只支持按主键进行删除。


```
def delete(tablename, params={}):
    sql = "delete from %s " % tablename
    sql += " where _id = %(_id)s "
    rs = exec_sql(sql, params)
    if rs[0]:
        return {"code": 200, "info": "delete success.", "total": rs[2]}
    else:
        return {"code": rs[1].args[0], "error": rs[1].args[1], "total": rs[2]}
```

### 中间层（baseDao）
提供默认的操作数据库接口，实现基础的业务逻辑，单表的CURD有它就足够了。有复杂业务逻辑时，继承它，进行扩展就可以了。


```
import dbhelper


class BaseDao(object):

    def __init__(self, table):
        self.table = table

    def retrieve(self, params={}, fields=[], session={}):
        return dbhelper.select(self.table, params)

    def create(self, params={}, fields=[], session={}):
        if '_id' in params and len(params) < 2 or '_id' not in params and len(params) < 1:      #检测参数是否合法
            return {"code": 301, "err": "The params is error."}
        return dbhelper.insert(self.table, params)

    def update(self, params={}, fields=[], session={}):
        if '_id' not in params or len(params) < 2:          #_id必须提供且至少有一修改项
            return {"code": 301, "err": "The params is error."}
        return dbhelper.update(self.table, params)

    def delete(self, params={}, fields=[], session={}):
        if '_id' not in params:  #_id必须提供
            return {"code": 301, "err": "The params is error."}
        return dbhelper.delete(self.table, params)
```

### 动态调用CURD
根据客户调用的rest方式不同，动态调用baseDao的相应方法，这个很关键，实现了它才能自动分配方法调用，才能只需要建立一个数据表，就自动提供CURD基本访问功能。还好，动态语言能很方便的实现这种功能，感慨一下，node.js更方便且符合习惯^_^


```
method = {
        "GET": "retrieve",
        "POST": "create",
        "PUT": "update",
        "DELETE": "delete"
    }
```



```
getattr(BaseDao(table), method[request.method])(params, [], {})
```

##### 说明：

- table是前一章中解析出来的数据表名，这块就是users；
- method应该是定义一个常量对象，对应rest的动词，因为对ypthon不熟，定义了一个变量先用着，查了下常量说明，看着好复杂；
- request.method 客户请求的实际rest动词；
- params是前一章中解析出来的参数对象；

### 完整代码

```
git clone https://github.com/zhoutk/pyrest.git
cd pyrest
export FLASK_APP=index.py
flask run
```

### 小结
至此，我们已经实现了基本的框架功能，以后就是丰富它的羽翼。比如：session、文件上传、跨域、路由改进（支持无缝切换操作数据库的基类与子类）、参数验证、基础查询功能增强（分页、排序、模糊匹配等）。
感慨一下，好怀念在node.js中json对象的写法，不用在key外加引号。

补丁
刚把基础数据库访问类中的insert方法的参数形式改成了字典，结果异常信息也正常了，文章不再改动，有兴趣者请自行查阅源代码。


