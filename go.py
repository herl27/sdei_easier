import requests
import re
import os
from aes import AESECB

class Connect(object):
    def __init__(self):
        self.CT_FORM = {'Content-Type': 'application/x-www-form-urlencoded'}
        self.session = requests.Session()
        UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:60.0) Gecko/20100101 Firefox/60.0'
        self.session.headers.update({'User-Agent': UA})

    def auth_password(self):
        login_page = self.session.get('http://www.sdei.edu.cn/uc/wcms/mobilelogin.htm')
        if login_page.status_code == requests.codes.ok:
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
                    if logging_in.status_code == requests.codes.ok:
                        pattern = re.compile('<title>(\S+)</title>')
                        if pattern.search(logging_in.text).group(1) == '正在登录':
                            return logging_in 
                        else:
                            print('登录失败')
                    else:
                        logging_in.raise_for_status()
                else:
                    print('请设置正确的环境变量')
            else:
                self.auth_password()
        else:
            login_page.raise_for_status()
