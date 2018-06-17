import requests
from bs4 import BeautifulSoup
import re
import os
from urllib.parse import urljoin
from aes import AESECB

class Connect(object):
    def __init__(self):
        self.error_message = None
        self.CT_FORM = {'Content-Type': 'application/x-www-form-urlencoded'}
        self.session = requests.Session()
        UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0'
        self.session.headers.update({'User-Agent': UA})

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.error_message:
            print(self.error_message)
        self.session.close()

    def login(self):
        page = self.session.get('http://szpj.sdei.edu.cn/zhszpj/web/index/yhIndex.htm')
        if page.status_code == 200:
            soup = BeautifulSoup(page.text, 'html.parser')
            # 判断是否已经登录
            if soup.title.string == '正在登录':
                page = self.auto_post(page.text)
                soup = BeautifulSoup(page.text, 'html.parser')
                if soup.title.string == "山东省教育云服务平台":
                    url = urljoin(page.url, soup.iframe['src'])
                    page = self.session.get(url)
                    soup = BeautifulSoup(page.text, 'html.parser')
                    form = soup.find(id='login_form')
                    post_data = {}
                    for input_ in form.find_all('input'):
                        post_data[input_['name']] = input_.get('value')
                    pattern = re.compile('var aesKey = "(\w+)"')
                    aes_key = re.search(pattern, page.text).group(1)
                    if aes_key:
                        username = os.getenv('LOGIN_USERNAME')
                        password = os.getenv('LOGIN_PASSWORD')
                        if username and password:
                            post_data['j_username'] = username
                            post_data['j_password'] = AESECB.encrypt(password, aes_key)
                        else:
                            self.error_message = '请设置环境变量'
                    else:
                        self.error_message = "未找到AES_KEY"
                    url = urljoin(page.url, form['action'])
                    page = self.session.post(url, data=post_data)
                    page = self.auto_post(page.text)
                    soup = BeautifulSoup(page.text, 'html.parser')
                    if soup.title.string == '欢迎使用综合素质评价系统':
                        m = re.search('(HHCSRFToken):"(.+)"', page.text)
                        self.session.headers.update({m.group(1): m.group(2)})
                else:
                    self.error_message = '数据获取错误'
                    print(soup.title.string)
            elif soup.title.string == '欢迎使用综合素质评价系统':
                print('已登录')
                m = re.search('(HHCSRFToken):"(.+)"', page.text)
                self.session.headers.update({m.group(1): m.group(2)})
            else:
               self.error_message = "获取数据异常，请稍后再试"
        else:
            self.error_message = "获取网页失败,请检查网络连接"

    def auto_post(self, html):
        param = {}
        soup = BeautifulSoup(html, 'html.parser')
        url = soup.form['action']
        for i in soup.find_all('input'):
            param[i['name']] = i['value']
        web = self.session.post(url, data=param)
        return web

    def query_stu(self, username=None, pageSize=10):
        url = 'http://szpj.sdei.edu.cn/zhszpj/jcsj/glry/yhgl.do?method=queryXszhList'
        data = {
                'level': None, 
                'xx_bjxx_id': None, 
                'page': '0', 
                'user_id': None, 
                'dir': None, 
                'xx_njxx_id': None, 
                'user_name': username, 
                'organld': '3709830003', 
                'sort': None, 
                'pageSize': str(pageSize)
                }
        if self.session.headers.get('HHCSRFToken'):
           query = self.session.post(url, data=data)
           if query.status_code == 200:
               return query.json()
           else:
               self.error_message = '数据查询失败'
        else:
            self.login()
            self.query_stuednt()
