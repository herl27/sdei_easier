import requests
import re
import os
from aes import AESECB

class Connect(object):
    def __init__(self):
        self.error_message = None
        self.title_pattern = re.compile('<title>(\S+)</title>')
        self.CT_FORM = {'Content-Type': 'application/x-www-form-urlencoded'}
        self.session = requests.Session()
        UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0'
        self.session.headers.update({'User-Agent': UA})

    def auth_password(self):
        login_page = self.session.get('http://www.sdei.edu.cn/uc/wcms/mobilelogin.htm')
        if login_page.status_code == requests.codes.ok and \
            self.title_pattern.search(login_page.text).group(1) == '欢迎使用':
            pattern = re.compile('var aesKey = "(\w+)"')
            aes_key = re.search(pattern, login_page.text).group(1)
            if aes_key:
                username = os.getenv('LOGIN_USERNAME')
                password = os.getenv('LOGIN_PASSWORD')
                if username and password:
                    param = {
                        'hid_remember_login_state': 0,
                        'hid_remember_me': 0,
                        'j_password': AESECB.encrypt(password, aes_key),
                        'j_username': username,
                        'login_salt': None,
                        'pwd': None,
                        'relayUrl': None,
                        'verify_code': None
                            }
                    logging_in = self.session.post('http://www.sdei.edu.cn/uc/j_hh_security_check',
                            data=param, headers=self.CT_FORM)
                    if logging_in.status_code == requests.codes.ok and \
                        self.title_pattern.search(logging_in.text).group(1) == '正在登录':
                        logging_in_2 = self.session.post('http://www.sdei.edu.cn/uc/DoSamlSso',
                                data=self.get_hidden_input(logging_in.text),
                                headers=self.CT_FORM)
                        sc = self.session.post('http://www.sdei.edu.cn/sc/UserAction',
                                data=self.get_hidden_input(logging_in_2.text),
                                headers=self.CT_FORM)
                        return sc
                    else:
                        self.error_message = "账号密码验证失败"
                else:
                    self.error_message = "请设置正确的环境变量"
            else:
                self.error_message = "未找到KEY"
        else:
            self.error_message = "登录页面打开错误"

    @staticmethod
    def get_hidden_input(html):
        param = {}
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        for i in soup.find_all('input'):
            param[i['name']] = i['value']
        return param
