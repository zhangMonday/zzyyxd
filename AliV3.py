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
# 代理配置 (已禁用)
# ==============================================================================
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
        
        # 初始化 Session
        self.session = requests.Session()
        
        # 初始化账号密码变量
        self.username = None
        self.password = None

        # 基础 Headers
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
        
        # 更新 Session 的基础 Headers
        self.session.headers.update(self.headers)

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

        # 这里的请求与 JLC 主站无关，使用普通的 requests 即可，也可以用 session
        response = requests.post('https://1tbpug.captcha-open.aliyuncs.com/', headers=self.headers, data=data,
                                 proxies=proxy)

        print(response.text)
        try:
            self.DeviceConfig = response.json()['DeviceConfig']
            print('DeviceConfig', self.DeviceConfig)
            self.CertifyId = response.json()['CertifyId']
            print('CertifyId', self.CertifyId)
            self.StaticPath = response.json()['StaticPath'] + '.js'
            print('StaticPath', self.StaticPath)
        except Exception as e:
            print(f"Req_Init Error: {e}")

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

    def Sumbit_All(self):
        args = MatchArgs(self.StaticPath)
        if args is None:
            print('StaticPath not found')
            if self.username and self.password:
                print("Retry executing main...")
                # 重试时不重新传入 cookies/headers，复用 session
                self.main(self.username, self.password)
            else:
                print("Error: Args missing for retry.")
            return

        print('dyn_key', args)
        _data = self.getData(args)
        deviceToekn = self.GetDeviceData()

        print('deviceToekn', deviceToekn)
        print('_data', _data)

        # 更新请求特定的 Headers
        self.session.headers.update({
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json',
            'origin': 'https://passport.jlc.com',
            'referer': 'https://passport.jlc.com/window/login?appId=JLC_PORTAL_PC&redirectUrl=https%3A%2F%2Fwww.jlc.com%2F',
            # secretkey 和 uuid 已经在 main 中通过 update headers 放入了 session
        })

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

        # 使用 Session 发送请求，自动携带 cookies
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

        # 更新 Headers
        self.session.headers.update({
            'accept': 'application/json, text/plain, */*',
            'content-type': 'application/json',
            'origin': 'https://passport.jlc.com',
            'referer': 'https://passport.jlc.com/window/login?appId=JLC_PORTAL_PC&redirectUrl=https%3A%2F%2Fwww.jlc.com%2F',
            # 移除所有硬编码的 Cookie 设置，完全依赖 Session
        })

        json_data = {
            'username': username,
            'password': password,
            'isAutoLogin': True,
            'captchaTicket': self.captchaTicket,
        }

        # 使用 Session 发送请求
        response = self.session.post(
            'https://passport.jlc.com/api/cas/login/with-password', 
            json=json_data
        )

        print(response.text)

    def main(self, username, password, cookies=None, headers=None):
        self.username = username
        self.password = password
        
        # 1. 设置 Cookies (如果传入)
        if cookies:
            print("Loading custom cookies into session...")
            requests.utils.add_dict_to_cookiejar(self.session.cookies, cookies)
        
        # 2. 设置 Headers (如果传入，主要覆盖 secretkey 和 uuid)
        if headers:
            print("Loading custom headers into session...")
            self.session.headers.update(headers)

        # 3. 阿里云验证流程
        self.Req_Init()
        self.decrypt_DeviceConfig()
        self.GetDynamic_Key()
        self.GetLog2()
        self.GetLog3()
        
        # 4. 获取验证码票据 (会更新 session cookie)
        res = self.Sumbit_All()
        
        # 5. 登录 (复用 session cookie)
        enc_username = pwdEncrypt(username)
        enc_password = pwdEncrypt(password)
        self.Login(enc_username, enc_password)
        return res


if __name__ == '__main__':
    ali = AliV3()
    if len(sys.argv) >= 3:
        ali.main(sys.argv[1], sys.argv[2])
    else:
        print("用法: python AliV3.py <username> <password>")
