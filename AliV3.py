import json
import os
import random
import subprocess
import time
import sys
from functools import partial

subprocess.Popen = partial(subprocess.Popen, encoding='utf-8', errors='ignore')

import requests
import execjs

from Utils import MatchArgs, pwdEncrypt

# ==============================================================================
# 修复：注释掉导致报错的代理获取代码
# 原代码在 import 时会请求 51daili.com 导致 ConnectionResetError
# ==============================================================================
# prox = requests.get(
#     'http://bapi.51daili.com/getapi2?linePoolIndex=-1&packid=2&time=2&qty=1&port=1&format=txt&usertype=17&uid=55442').text
#
# print(prox)

# prox = ''

# proxy = {
#     "https": "http://" + prox,
#     "http": "http://" + prox,
# }
proxy = None
# ==============================================================================


class AliV3:
    def __init__(self):
        self.captchaTicket = None
        self.StaticPath = None
        self.CertifyId = None
        self.Dynamic_Key = None
        self.fenlin = None
        self.fenlin_path = None
        self.Real_Config = None
        self.DeviceConfig = None
        self.sign_key1 = "YSKfst7GaVkXwZYvVihJsKF9r89koz"
        self.sign_key2 = "fpOKzILEajkqgSpr9VvU98FwAgIRcX"
        self.author = '古月'
        
        # 初始化账号密码变量，用于在 Sumbit_All 中重试时调用
        self.username = None
        self.password = None

        # 初始化 Session 对象，用于管理 Cookie
        self.session = requests.Session()

        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'Content-Type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'Origin': 'https://account.dji.com',
            'Pragma': 'no-cache',
            'Referer': 'https://account.dji.com/',
            'Sec-Fetch-Dest': 'empty',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Site': 'cross-site',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0',
            'sec-ch-ua': '"Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        }

    def get_sign(self, params, key):
        with open('sign.js', 'r', encoding='utf-8') as f:
            js = f.read()
        ctx = execjs.compile(js)
        return ctx.call('Sign', params, key)

    def getDeviceData(self, ):
        with open('sign.js', 'r', encoding='utf-8') as f:
            js = f.read()
        ctx = execjs.compile(js)
        return ctx.call('getDeviceData')

    def Req_Init(self):
        data = {
            'AccessKeyId': 'LTAI5tSEBwYMwVKAQGpxmvTd',
            'SignatureMethod': 'HMAC-SHA1',
            'SignatureVersion': '1.0',
            'Format': 'JSON',
            'Timestamp': '2025-12-15T13:30:27Z',
            'Version': '2023-03-05',
            'Action': 'InitCaptchaV3',
            'SceneId': '6mw4mrmg',
            'Language': 'cn',
            'Mode': 'embed',
        }

        DeviceData = self.getDeviceData()
        data['DeviceData'] = DeviceData
        data = self.get_sign(data, self.sign_key1)

        response = requests.post('https://1tbpug.captcha-open.aliyuncs.com/', headers=self.headers, data=data,
                                 proxies=proxy)

        print(response.text)
        self.DeviceConfig = response.json()['DeviceConfig']
        print('DeviceConfig', self.DeviceConfig)
        self.CertifyId = response.json()['CertifyId']
        print('CertifyId', self.CertifyId)
        self.StaticPath = response.json()['StaticPath'] + '.js'
        print('StaticPath', self.StaticPath)

    def decrypt_DeviceConfig(self):
        with open('AliyunCaptcha.js', 'r', encoding='utf-8') as f:
            js = f.read()
        ctx = execjs.compile(js)
        self.Real_Config = ctx.call('getDeviceConfig', self.DeviceConfig)
        print('Real_Config', self.Real_Config)
        self.fenlin_path = self.Real_Config['version'] + '.js'

    def GetDynamic_Key(self):
        self.fenlin = 'https://g.alicdn.com/captcha-frontend/FeiLin/' + self.fenlin_path
        print(self.fenlin)

        fenlin_js = requests.get(self.fenlin).text
        with open('fenlin.js', 'r', encoding='utf-8') as f:
            js = f.read()

        jscode = js.replace('#jscode#', fenlin_js)
        jscode = jscode.replace('#config#', self.DeviceConfig)
        
        filename = f'fenlin_temp_{self.CertifyId}.js'
        filepath = os.path.join('./temp', filename)

        # 确保temp目录存在
        if not os.path.exists('./temp'):
            os.makedirs('./temp')

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(jscode)

        result = subprocess.run(
            ["node", filepath],
            capture_output=True,
            text=True
        ).stdout
        self.Dynamic_Key = result.replace('\n', '')
        print(self.Dynamic_Key)

    def GetLog2(self):
        data = {
            'AccessKeyId': 'LTAI5tGjnK9uu9GbT9GQw72p',
            'Version': '2020-10-15',
            'SignatureMethod': 'HMAC-SHA1',
            'SignatureVersion': '1.0',
            'Format': 'JSON',
            'Action': 'Log2',
        }
        with open('Log2_Data.js', 'r', encoding='utf-8') as f:
            js = f.read()
        ctx = execjs.compile(js)

        env_folder = 'env'
        json_files = [f for f in os.listdir(env_folder) if f.endswith('.json')]
        random_json_file = random.choice(json_files)
        json_file_path = os.path.join(env_folder, random_json_file)

        with open(json_file_path, 'r', encoding='utf-8') as f:
            env_data = json.load(f)

        print(f'随机选择的环境文件: {random_json_file}')
        data = ctx.call('getLog2Data', data, self.Dynamic_Key, self.Real_Config, env_data)
        print(data)
        response = requests.post('https://cloudauth-device-dualstack.cn-shanghai.aliyuncs.com/', headers=self.headers,
                                 data=data, proxies=proxy)
        print(response.text)

    def GetLog3(self):
        data = {
            'AccessKeyId': 'LTAI5tGjnK9uu9GbT9GQw72p',
            'Version': '2020-10-15',
            'SignatureMethod': 'HMAC-SHA1',
            'SignatureVersion': '1.0',
            'Format': 'JSON',
            'Action': 'Log3',
        }
        with open('Log3_Data.js', 'r', encoding='utf-8') as f:
            js = f.read()
        ctx = execjs.compile(js)
        data = ctx.call('getLog3Data', data, self.Real_Config)
        print(data)

        response = requests.post('https://cloudauth-device-dualstack.cn-shanghai.aliyuncs.com/', headers=self.headers,
                                 data=data, proxies=proxy)
        print(response.text)

    def GetDeviceData(self):
        with open('deviceToken.js', 'r', encoding='utf-8') as f:
            js = f.read()
        ctx = execjs.compile(js)
        DeviceToken = ctx.call('getDeviceToken', self.Real_Config, self.Dynamic_Key)
        return DeviceToken

    def getData(self, args):
        with open('data.js', 'r', encoding='utf-8') as f:
            js = f.read()
        ctx = execjs.compile(js)
        data = ctx.call('getData', args, self.CertifyId)
        print(data)
        return data

    def Init_JLC_Connection(self):
        """
        请求 passport.jlc.com 获取实时的 Cookie 和 Header
        """
        print("Initializing JLC Session...")
        login_url = 'https://passport.jlc.com/window/login?appId=JLC_PORTAL_PC&redirectUrl=https%3A%2F%2Fwww.jlc.com%2F'
        
        # 模拟浏览器访问页面的 Header
        self.session.headers.update({
            'User-Agent': self.headers['User-Agent'],
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': self.headers['Accept-Language'],
            'Upgrade-Insecure-Requests': '1',
            'Connection': 'keep-alive'
        })

        # 发送 GET 请求以获取 Cookies
        self.session.get(login_url)
        
        # 更新 Header 为 API 请求所需的格式
        self.session.headers.update({
            'Accept': 'application/json, text/plain, */*',
            'Content-Type': 'application/json',
            'Origin': 'https://passport.jlc.com',
            'Referer': login_url,
        })
        
        # 移除页面请求特有的 Header
        if 'Upgrade-Insecure-Requests' in self.session.headers:
            del self.session.headers['Upgrade-Insecure-Requests']
            
        print("Session Initialized.")

    def Sumbit_All(self):
        args = MatchArgs(self.StaticPath)
        if args is None:
            print('StaticPath not found')
            # 重试逻辑：使用保存的 self.username 和 self.password
            if self.username and self.password:
                print("Retry executing main...")
                self.main(self.username, self.password)
            else:
                print("Error: Args missing for retry.")
            return

        print('dyn_key', args)
        _data = self.getData(args)
        deviceToekn = self.GetDeviceData()

        print('deviceToekn', deviceToekn)
        print('_data', _data)

        # 已移除固定的 cookies 和 headers，使用 self.session 自动处理

        captcha_verify_param = {
            "sceneId": "6mw4mrmg",
            "certifyId": self.CertifyId,
            "deviceToken": deviceToekn,
            "data": _data
        }

        captcha_verify_param_str = json.dumps(captcha_verify_param, separators=(',', ':'))

        json_data = {
            'captchaVerifyParam': captcha_verify_param_str,
            'sceneType': 'pass_word_login',
            'aliyunSceneId': '6mw4mrmg',
        }

        # 使用 session 发送请求，header 和 cookie 会自动携带
        response = self.session.post(
            'https://passport.jlc.com/api/cas/captcha/v2/check-ali-captcha',
            json=json_data
        )

        print(response.status_code)
        print(response.text)
        
        try:
            self.captchaTicket = response.json()['data']['captchaTicket']
        except Exception as e:
            print("Failed to get captchaTicket:", e)

    def Login(self, username, password):
        if not self.captchaTicket:
            print("Skipping login: No captchaTicket acquired.")
            return

        # 已移除固定的 cookies 和 headers，使用 self.session 自动处理

        json_data = {
            'username': username,
            'password': password,
            'isAutoLogin': True,
            'captchaTicket': self.captchaTicket,
        }

        # 使用 session 发送请求
        response = self.session.post(
            'https://passport.jlc.com/api/cas/login/with-password', 
            json=json_data
        )

        print(response.text)

    def test(self):
        pass

    def main(self, username, password):
        # 保存参数到实例变量
        self.username = username
        self.password = password
        
        # 1. 先初始化 JLC 的连接，获取实时 Cookie 和 Header
        self.Init_JLC_Connection()

        # 使用 self 调用实例方法，不再重新实例化 AliV3
        self.Req_Init()
        self.decrypt_DeviceConfig()
        self.GetDynamic_Key()
        self.GetLog2()
        self.GetLog3()
        
        res = self.Sumbit_All()
        
        # 传递加密后的账号密码进行登录
        enc_username = pwdEncrypt(username)
        enc_password = pwdEncrypt(password)
        self.Login(enc_username, enc_password)
        return res


if __name__ == '__main__':
    ali = AliV3()
    
    # 检查命令行参数，如果有则使用，如果没有则提示
    if len(sys.argv) >= 3:
        user_arg = sys.argv[1]
        pass_arg = sys.argv[2]
        ali.main(user_arg, pass_arg)
    else:
        print("用法: python AliV3.py <username> <password>")
        print("示例: python AliV3.py 13800138000 MyPassword123")
