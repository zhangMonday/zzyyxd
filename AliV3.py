import json
import os
import random
import subprocess
import time
import sys
import uuid  # 新增：用于生成随机设备ID
from functools import partial

subprocess.Popen = partial(subprocess.Popen, encoding='utf-8', errors='ignore')

import requests
import execjs

from Utils import MatchArgs, pwdEncrypt

# 代理配置
proxy = None

class AliV3:
    def __init__(self):
        # 1. 初始化 Session
        self.session = requests.Session()
        
        # 2. 【关键修复】生成随机的设备ID和客户端UUID
        # 必须保持整个会话期间一致，否则滑块验证会失败
        self.device_id = str(uuid.uuid4()).replace('-', '')
        self.client_uuid = f"{str(uuid.uuid4())}-{int(time.time()*1000)}"
        
        print(f"初始化虚拟设备 ID: {self.device_id}")
        
        # 3. 将 device_id 注入到 session 的 cookies 中
        # 这是之前报 500 错误的根本原因：缺少 device_id
        self.session.cookies.set('device_id', self.device_id, domain='passport.jlc.com')
        self.session.cookies.set('device_id', self.device_id, domain='.jlc.com')

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
        
        self.username = None
        self.password = None

        # 更新 Session 的 headers
        self.headers = {
            'Accept': '*/*',
            'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
            'sec-ch-ua': '"Chromium";v="122", "Not(A:Brand";v="24", "Microsoft Edge";v="122"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            # 注入客户端 UUID
            'x-jlc-clientuuid': self.client_uuid
        }
        self.session.headers.update(self.headers)

    def Init_Session(self):
        print("正在初始化会话，获取基础 Cookies...")
        # 访问一个简单的页面获取 acw_tc 等基础 cookie
        url = "https://passport.jlc.com/window/login?appId=JLC_PORTAL_PC"
        try:
            self.session.get(url, verify=False, timeout=10)
            # print("Cookies 更新:", self.session.cookies.get_dict())
        except Exception as e:
            print(f"初始化 Cookies 警告 (不影响继续): {e}")

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

        # 阿里云请求不需要带 JLC 的 cookies，这里用裸 requests 发送或者新建 session 也可以
        # 但为了简单，直接用 requests，反正不共享 cookie 给 jlc 也没事
        response = requests.post('https://1tbpug.captcha-open.aliyuncs.com/', headers=self.headers, data=data, proxies=proxy)

        # print(response.text)
        self.DeviceConfig = response.json()['DeviceConfig']
        self.CertifyId = response.json()['CertifyId']
        self.StaticPath = response.json()['StaticPath'] + '.js'
        print('CertifyId', self.CertifyId)

    def decrypt_DeviceConfig(self):
        with open('AliyunCaptcha.js', 'r', encoding='utf-8') as f:
            js = f.read()
        ctx = execjs.compile(js)
        self.Real_Config = ctx.call('getDeviceConfig', self.DeviceConfig)
        self.fenlin_path = self.Real_Config['version'] + '.js'

    def GetDynamic_Key(self):
        self.fenlin = 'https://g.alicdn.com/captcha-frontend/FeiLin/' + self.fenlin_path
        
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

        result = subprocess.run(["node", filepath], capture_output=True, text=True).stdout
        self.Dynamic_Key = result.replace('\n', '')

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

        data = ctx.call('getLog2Data', data, self.Dynamic_Key, self.Real_Config, env_data)
        requests.post('https://cloudauth-device-dualstack.cn-shanghai.aliyuncs.com/', headers=self.headers, data=data, proxies=proxy)

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

        requests.post('https://cloudauth-device-dualstack.cn-shanghai.aliyuncs.com/', headers=self.headers, data=data, proxies=proxy)

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
        return data

    def Sumbit_All(self):
        args = MatchArgs(self.StaticPath)
        if args is None:
            print('StaticPath not found, retrying...')
            if self.username and self.password:
                self.main(self.username, self.password)
            return

        _data = self.getData(args)
        deviceToekn = self.GetDeviceData()

        # 这里的 Headers 使用 session 默认的即可，只需补充特有的
        # 注意：secretkey 依然保留硬编码，如果还报错可能需要更新它
        headers_override = {
            'content-type': 'application/json',
            'referer': 'https://passport.jlc.com/window/login?appId=JLC_PORTAL_PC&redirectUrl=https%3A%2F%2Fwww.jlc.com%2F',
            'secretkey': '35616236663038352d643366382d343131662d396239622d366439643132653639373764',
        }

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

        # 使用 session 发送，确保带上 device_id 和 acw_tc
        response = self.session.post(
            'https://passport.jlc.com/api/cas/captcha/v2/check-ali-captcha',
            headers=headers_override,
            json=json_data
        )

        print("验证码检查状态:", response.status_code)
        
        try:
            self.captchaTicket = response.json()['data']['captchaTicket']
            print(f"获取到 Ticket: {self.captchaTicket}")
        except Exception as e:
            print("获取 Ticket 失败:", response.text)

    def Login(self, username, password):
        if not self.captchaTicket:
            print("无法登录: 未获取到 captchaTicket")
            return

        headers_override = {
            'content-type': 'application/json',
            'referer': 'https://passport.jlc.com/window/login?appId=JLC_PORTAL_PC&redirectUrl=https%3A%2F%2Fwww.jlc.com%2F',
            'secretkey': '35616236663038352d643366382d343131662d396239622d366439643132653639373764',
        }

        json_data = {
            'username': username,
            'password': password,
            'isAutoLogin': True,
            'captchaTicket': self.captchaTicket,
        }

        print("正在尝试登录接口...")
        response = self.session.post(
            'https://passport.jlc.com/api/cas/login/with-password', 
            headers=headers_override, 
            json=json_data
        )

        print("登录结果:", response.text)

    def main(self, username, password):
        self.username = username
        self.password = password

        # 1. 初始化，生成 device_id 并注入
        self.Init_Session()

        # 2. 阿里云流程
        self.Req_Init()
        self.decrypt_DeviceConfig()
        self.GetDynamic_Key()
        self.GetLog2()
        self.GetLog3()
        
        # 3. 提交给嘉立创验证
        self.Sumbit_All()
        
        # 4. 登录
        enc_username = pwdEncrypt(username)
        enc_password = pwdEncrypt(password)
        self.Login(enc_username, enc_password)


if __name__ == '__main__':
    ali = AliV3()
    if len(sys.argv) >= 3:
        user_arg = sys.argv[1]
        pass_arg = sys.argv[2]
        ali.main(user_arg, pass_arg)
    else:
        print("请提供账号密码")
