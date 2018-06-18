import requests
from bs4 import BeautifulSoup
import re
import os
from urllib.parse import urljoin
from aes import AESECB

class Sdei(object):
    def __init__(self):
        self.url = {
                'sdei': 'http://www.sdei.edu.cn/sc/',
                'zhpj': 'http://szpj.sdei.edu.cn/zhszpj/',
                'query_stu': 'http://szpj.sdei.edu.cn/zhszpj/jcsj/glry/yhgl.do?method=queryXszhList',
                'change_pwd': 'http://szpj.sdei.edu.cn/zhszpj/jcsj/uc/initPwd.do?method=initPwd',
                'xk': 'http://www.sdei.edu.cn/gkzx/wsc/undergraduateMajor.htm',
                'lq': 'http://www.sdei.edu.cn/gkzx/wsc/matriculate.htm'
                }
        self.is_login = False
        self.action_xk = False
        self.action_lq = False
        self.message = None
        self.session = requests.Session()
        UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0'
        self.session.headers.update({'User-Agent': UA})
        self.login()
        if self.is_login == False:
            raise Exception('登录失败')

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.message:
            print(self.message)
        self.session.close()

    @staticmethod
    def title(resp):
        pattern_title = re.compile('<title>(.+)</title>')
        return pattern_title.search(resp.text).group(1)

    def update_token(self, resp):
        pattern_token = re.compile('(HHCSRFToken):"(.+)"')
        m = pattern_token.search(resp.text)
        if m:
            self.session.headers.update({m.group(1): m.group(2)})
            return True

    def login(self):
        # 访问云平台首页
        response = self.session.get('http://www.sdei.edu.cn')
        if response.status_code == 200 and \
            self.title(response) == "山东省教育云服务平台":
            # 获取登录框iframe页面URL，并访问
            url = urljoin(response.url,
                re.search('iframe id="login-iframe".+? src="(.+?)"',
                    response.text).group(1))
            response = self.session.get(url)
            if response.status_code == 200 and \
                self.title(response) == "欢迎使用":
                # 将Token加入到headers中
                self.update_token(response)
                aes_key = re.search('var aesKey = "(\w+)"',
                    response.text).group(1)
                username = os.getenv('LOGIN_USERNAME')
                password = os.getenv('LOGIN_PASSWORD')
                if username and password:
                    response = self.post(response, allow_redirects=False,
                        j_username=username,
                        j_password=AESECB.encrypt(password, aes_key))
                    self.is_login = True
                    self.message = "登录成功"
                else:
                    self.message = '请设置环境变量'
            else:
                self.message = "登录页面获取失败"
        else:
            self.message = "获取网页失败,请检查网络连接"
        print(self.message)

    def post(self, response, allow_redirects=True, **kwargs):
        param = {}
        form = BeautifulSoup(response.text, 'html.parser').form
        for i in form.find_all('input'):
            param[i['name']] = i.get('value')
        if kwargs:
            param.update(kwargs)
        url = urljoin(response.url, form['action'])
        resp = self.session.post(url, 
            allow_redirects=allow_redirects, data=param)
        if resp.status_code == 200 and \
            self.title(resp) == "正在登录":
            resp = self.post(resp)
        return resp

    def get(self, url):
        resp = self.session.get(url)
        if resp.status_code == 200 and \
            self.title(resp) == "正在登录":
            resp = self.post(resp)
        return resp

    def activate(self, key):
        resp = self.get(self.url[key])
        if resp.status_code == 200:
            if self.update_token(resp):
                if self.title(resp) == "欢迎使用综合素质评价系统":
                    self.action_zhpj = True
                    self.message = "综评应用激活成功"
                elif self.title(resp) == "普通高校本科各专业类录取情况查询": 
                    self.action_lq = True
                    self.message = "录取应用激活成功"
                elif self.title(resp) == "高校选考科目要求查询":
                    self.action_xk = True
                    self.message = "选科应用激活成功"
                else:
                    self.message = "未知应用"
            else:
                self.message = "应用激活失败"
        else:
            self.message = '网络连接失败，无法激活应用'
        print(self.message)

    def query_stu(self, user=None, pageSize=10):
        if not self.action_zhpj:
            self.activate('zhpj')
        if user.isdigit():
            username = None
            user_id = user
        else:
            username = user
            user_id = None
        data = {
            'level': None, 
            'xx_bjxx_id': None, 
            'page': '0', 
            'user_id': user_id, 
            'dir': None, 
            'xx_njxx_id': None, 
            'user_name': username, 
            'organld': '3709830003', 
            'sort': None, 
            'pageSize': str(pageSize)
                }
        query = self.session.post(self.url['query_stu'], data=data)
        if query.status_code == 200:
            self.message = "学生信息查询成功" 
            return query.json()
        elif query.status_code == 403:
            self.activate('zhpj')
            self.message = "学生信息查询成功"
            return self.query_stu(user=user, pageSize=pageSize)
        else:
            self.message = '数据查询失败'
        print(self.message)

    def change_pwd(self, uid, user_id, newpwd='12345678'):
        data = {
                'list[0].uid': uid,
                'list[0].userId': user_id,
                'newPwd': newpwd
                }
        resp = self.session.post(self.url['change_pwd'], data=data)
        return resp
        if resp.status_code == 200 and resp.json()['rc'] == '0':
            self.message = "密码重置成功"
            return True
        else:
            self.message = "密码重置失败"
            print(self.message)

