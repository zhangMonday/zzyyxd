import json
import os
import random
import subprocess
import time
from functools import partial

subprocess.Popen = partial(subprocess.Popen, encoding='utf-8', errors='ignore')

import requests
import execjs

from Utils import MatchArgs, pwdEncrypt

prox = requests.get(
    'http://bapi.51daili.com/getapi2?linePoolIndex=-1&packid=2&time=2&qty=1&port=1&format=txt&usertype=17&uid=55442').text

print(prox)

# prox = ''

proxy = {
    "https": "http://" + prox,
    "http": "http://" + prox,
}
proxy = None


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
            # 'DeviceData': 'byAgDBTTWK6iQ63aLnMRvywYbJ50c453wUz9CdNf4pWB+H4EOu7koqzwbASi1Zy3UAiN5BAy67x6IpkMZp68saoXZCmnYPMyD49L0BugfwoRBbb9XN0l0xI16fBTApsQKcrtPw0l22ImeYW31SFQyJsfOzDjNz+7lyK9e8g3QOgpm/ZEReXA2IfqqlGdm2ee',
            # 'SignatureNonce': 'f9a808a6-6847-4cfa-8100-0b6cfa6ffb80',
            # 'Signature': 'Czd7sbR/LbszBB/eOR5ImoMdGag=',
        }

        DeviceData = self.getDeviceData()

        # print("DeviceData", DeviceData)

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
        # print(fenlin_js)

        with open('fenlin.js', 'r', encoding='utf-8') as f:
            js = f.read()

        jscode = js.replace('#jscode#', fenlin_js)
        jscode = jscode.replace('#config#', self.DeviceConfig)
        # 文件名为 fenlin_temp + self.CertifyId

        filename = f'fenlin_temp_{self.CertifyId}.js'
        filepath = os.path.join('./temp', filename)

        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(jscode)

        result = subprocess.run(
            ["node", filepath],  # 将参数直接作为列表中的一部分
            capture_output=True,  # 捕获标准输出
            text=True  # 返回输出为字符串格式
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

        # 随机读取env文件夹下的json文件获取值
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
            # 'Data': '0blQ85dGJrY0HYY8GlS4tTBVuksZpLI2N7miYiBeU9uZjyZRhAxOvz0T49gSNTS83zKHlE+DvtFaPDnaiZiFalD3bmcfEmePX0lmZeCEvaKHm3qE7ivkzKbFROwt8VZIrYEKAiW8OBVdA8MCC56XcLi4kBbKWuFwJ+/C/n7gUbLrgee268Pq8+0gAofxUTMmKAWK8deCCXivr7YL2ooQyhBa3Ksuz9omHwQ+0oDjdnvhrRnWnVcQrJOcDmifgSyZb6pI6BcECczEWX+eBO6m7D8R80xeO5cqK3GjYjp9ii3jBsL6hPQTkwXvz7j/bWF5KSHzktPfYhZ4aO349eC3bUz11XhAEW0EUr/yruZAdToW+gbuVY6tQMPMHeaTxtZNnIfbyrakDhSQqZL4gqJ3JvnfOui1BMZ9QdaLnbgN6JtfhSt4RKJISoNDR6xXgF9nM9Prw+ZTi9JrZIRvJ2qnKdWGPv3kRes3nQOX5Giu1MA9X+GQL4eQ2z3Dl9aLPESdNnwjadiN7vLxLZlY2+6g/MTzxKUGe/4S1jBL028vcUgGRUhPURU489cUbvejZQy52f5keMOvdy88/7TIg1ZvpZ7XexDma0mleMBjYqrQcvUNRPHhRxLT3IEt49leh39/WPGJkzqk0e5NqMlo904Svhd5E5STOje4RtyudPeygvllxqU0JtN0zrRpJ0VCIizIxgngzWnw//iHptxrLqzp7Apc9pc+VlR81g2HwulPQLpPItt+rstE8Nzamj2LJQeQEFOWl49d3BDC3zq+JZEvkN4x7woT754oQZQ2bNHM/GLk316c+wSvXU3lQSEZ0Zv38008Lm/hPHnP5hU1Kfsi2E7BGWrdQ4cYdEgv7/BQCpPzZ5ZCrePZZ9jRH7KiI3t532CgZxfdZV6WaOc+zF3W2Ri2qOL/cg8+6dOPsPT4fFuEa6ILO8lmnTPoflGye+sGOmXNsneyW//o71JNtKI6nVkh58Q5ocF4OkM2TqZE5DMtscVo7fPYkq0BFGsLizlkJ6g+r3Ys+91u8RZqbiXqkS2Y18NCf2A5bbRB8rqFzmS0wOlKzUjkLWbdotZcdnBs+2G/Ox0YiXHj6sMYxfMRgEly8Qz4LyFka2fJU040ZOeE4BKhbtAlZf75gSbkwduqJ9h/4cNCVeW4E0gIU/ozTJdJ5k7+CDYvJcPsgZWOItq87xpJ361PDQmGnvfldcqSYKxhgrEYBAPl7ETUdsflW5e3MNpEKl5Y5tmB4VOf28E1Xl+fWaEG0dR02Tv0Itx03ZRIUUMa9Bd/u7HMkHsGXlVQKal9IMVmx1RkGPoYKIh4SC10l6J2ZXfP/liWkM6n0KjavHlI4EyPFpc7Z31ZXWTn94XAhy1Wj3raQBG0O12+SislsLeUeN4JGub6xTPiCJ9rJAkzTmMpAOLIp9DxJKFaSHUZZ4hw8kD5QS2FOzBvgQ2daGVQLFmQy3BWKyOND0knktsYPEKEuTbdIAk3DPxDNLUiqp3VwfWG0AvyS3dzMGI2pMop4Nf3os//2XS9dPktsEzBYDIuwmK2UIMFJN38aT/fRPfMqxTWGObfhggJOy7hCaTdFVyF4phCSHuAGzvnOyEoAxtgUqBqYpzmze6gEchcSAhnbkG4ujAzBX7rLIV0HxMwwTKg4dSArqUP8KRAJRhZIli3K8pceRryUZGe5Wgqm/qPwLDcm+WBNxDorS6k4QhqcSjO/+08vvBpGSeDWcy37Lt0G2wWsOLHgqHcCMIOmOgs4JX2gUBcgWo=',
            # 'SignatureNonce': '9f9dfa40-59b7-453e-9cfb-bcdd3e10b88d',
            # 'Signature': '86n7vhE7EdTHru+7OK3z+cIaoic=',
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
        # print(DeviceToken)
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
            self.main()
            return
        print('dyn_key', args)
        _data = self.getData(args)

        deviceToekn = self.GetDeviceData()

        print('deviceToekn', deviceToekn)
        print('_data', _data)

        import requests

 cookies = {
    'JSESSIONID': '',
    'AGL_USER_ID': '87ba0775-1be1-44f1-9e39-dc7b2d51e1d1',
    'acw_tc': '0ae5a7e017666808306043912ee4530e7b76c9a082a46f807ac310b7471739',
    'Hm_lvt_e2986f4b6753d376004696a1628713d2': '1766596836,1766673406,1766679921,1766680055',
    'Qs_lvt_290854': '1766680832',
    '__sameSiteCheck__': '1',
    'device_id': 'f3ad246f67dd4c2bbfadacba151890f8',
    'mediav': '%7B%22eid%22%3A%22586266%22%2C%22ep%22%3A%22%22%2C%22vid%22%3A%22%22%2C%22ctn%22%3A%22%22%2C%22vvid%22%3A%22%22%2C%22_mvnf%22%3A1%2C%22_mvctn%22%3A0%2C%22_mvck%22%3A1%2C%22_refnf%22%3A1%7D',
    'Hm_lvt_2c39bff195277b6ae5c091fa1a0539c9': '1766597985,1766673834,1766680810,1766680859',
    'HMACCOUNT': '5C0A50FD0F0FF06D',
    'Hm_lvt_fd32df1c0976b3b5c48e7972938e570a': '1766597985,1766673834,1766680810,1766680859',
    'Hm_lpvt_fd32df1c0976b3b5c48e7972938e570a': '1766680889',
    'Hm_lpvt_2c39bff195277b6ae5c091fa1a0539c9': '1766680889',
    'Hm_lpvt_e2986f4b6753d376004696a1628713d2': '1766680984',
    'Qs_pv_290854': '3642147226830568400%2C3099776345320113000%2C1163839156312501500%2C2168839663199811600%2C2658413402970838500',
    '_c_WBKFRo': 'EezND3oJZC7W3JqCMTUpu3siI7wbtDdCLwF3Ftuc',
    '_nb_ioWEgULi': '',
    'lsId': '018f1ea183a7449fa4e75ec02c145d40',
}

headers = {
    'accept': 'application/json, text/plain, */*',
    'accept-language': 'zh-CN',
    'cache-control': 'no-cache, no-store, must-revalidate',
    'content-type': 'application/json',
    # 'cookie': 'JSESSIONID=; AGL_USER_ID=87ba0775-1be1-44f1-9e39-dc7b2d51e1d1; acw_tc=0ae5a7e017666808306043912ee4530e7b76c9a082a46f807ac310b7471739; Hm_lvt_e2986f4b6753d376004696a1628713d2=1766596836,1766673406,1766679921,1766680055; Qs_lvt_290854=1766680832; __sameSiteCheck__=1; device_id=f3ad246f67dd4c2bbfadacba151890f8; mediav=%7B%22eid%22%3A%22586266%22%2C%22ep%22%3A%22%22%2C%22vid%22%3A%22%22%2C%22ctn%22%3A%22%22%2C%22vvid%22%3A%22%22%2C%22_mvnf%22%3A1%2C%22_mvctn%22%3A0%2C%22_mvck%22%3A1%2C%22_refnf%22%3A1%7D; Hm_lvt_2c39bff195277b6ae5c091fa1a0539c9=1766597985,1766673834,1766680810,1766680859; HMACCOUNT=5C0A50FD0F0FF06D; Hm_lvt_fd32df1c0976b3b5c48e7972938e570a=1766597985,1766673834,1766680810,1766680859; Hm_lpvt_fd32df1c0976b3b5c48e7972938e570a=1766680889; Hm_lpvt_2c39bff195277b6ae5c091fa1a0539c9=1766680889; Hm_lpvt_e2986f4b6753d376004696a1628713d2=1766680984; Qs_pv_290854=3642147226830568400%2C3099776345320113000%2C1163839156312501500%2C2168839663199811600%2C2658413402970838500; _c_WBKFRo=EezND3oJZC7W3JqCMTUpu3siI7wbtDdCLwF3Ftuc; _nb_ioWEgULi=; lsId=018f1ea183a7449fa4e75ec02c145d40',
    'expires': '0',
    'jsec-x-df': '04b9e7df40d6d227fae8a1c32a2d3bd496a93bf475795a00e417d32da7ae66a331738c49387bbadbf12e7980dbdd59d6a47825ff49686b3a6f5b7fc46c62684df6f3f44472b56421a0bbe4e7b2f9aa6f2bca662595d316f6b64261f2703a4f5a23b939a468f60e79ab690b2fca7f3f0657c6bf334a82297fb319bce5fca17f6835f9b5b0b9aa2e3b724b114a87',
    'origin': 'https://passport.jlc.com',
    'pragma': 'no-cache',
    'priority': 'u=1, i',
    'referer': 'https://passport.jlc.com/login?appId=JLC_OSHWHUB&redirectUrl=https%3A%2F%2Foshwhub.com%2Fsign_in&backCode=1',
    'sec-ch-ua': '"Chromium";v="127", "Not)A;Brand";v="99", "Microsoft Edge Simulate";v="127", "Lemur";v="127"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"Linux"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'secretkey': '31323237396563332d653163392d346237642d613939312d653339313634383861333839',
    'support-cookie-samesite': 'true',
    'user-agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    'x-jlc-clientinfo': 'eyJjbGllbnRUeXBlIjoiUEMtV0VCIiwib3NOYW1lIjoiTGludXgiLCJvc1ZlcnNpb24iOiJ4ODZfNjQiLCJicm93c2VyTmFtZSI6IkNocm9tZSIsImJyb3dzZXJWZXJzaW9uIjoiMTI3LjAuMC4wIiwiYnJvd3NlckVuZ2luZSI6IkJsaW5rIiwiYnJvd3NlckVuZ2luZVZlcnNpb24iOiIxMjcuMC4wLjAiLCJzY3JlZW5XaWR0aCI6MzYwLCJzY3JlZW5IZWlnaHQiOjY0MCwiZHByIjoyLjQwMTcwNzY0OTIzMDk1NywiY29sb3JEZXB0aCI6MjQsInBpeGVsRGVwdGgiOjI0LCJncHVWZW5kb3IiOiJHb29nbGUgSW5jLiAoQVJNKSIsImdwdVJlbmRlcmVyIjoiQU5HTEUgKEFSTSwgTWFsaS1HNzEsIE9wZW5HTCBFUyAzLjIpIiwiY3B1QXJjaGl0ZWN0dXJlIjoiYW1kNjQiLCJoYXJkd2FyZUNvbmN1cnJlbmN5Ijo4LCJsYW5ndWFnZSI6InpoLUNOIiwidGltZVpvbmUiOiJBc2lhL1NoYW5naGFpIiwidGltZXpvbmVPZmZzZXQiOi00ODAsIm5ldFR5cGUiOiI0ZyJ9',
    'x-jlc-clientuuid': '42f83515-8992-4e98-a3e6-f8bfc91f5b84-1752063435643',
}

        # captchaVerifyParam 是一个字典，而不是字符串
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

        response = requests.post(
            'https://passport.jlc.com/api/cas/captcha/v2/check-ali-captcha',
            cookies=cookies,
            headers=headers,
            json=json_data
        )

        print(response.status_code)
        print(response.text)
        self.captchaTicket = response.json()['data']['captchaTicket']

    def Login(self, username, password):
        import requests

        cookies = {
            'JSESSIONID': '',
            'device_id': 'c7d0a5f4b554477fae0e1ba29f84fb63',
            'HWWAFSESID': 'bcd7d8b4f625fb57ac',
            'HWWAFSESTIME': '1766299533105',
            'Qs_lvt_290854': '1766237893%2C1766299553',
            'Qs_pv_290854': '2499244294467079700%2C852781256760664000',
            '__sameSiteCheck__': '1',
            '_c_WBKFRo': '03ctatXDH7wXL1GIRpFWI9AUfuGhSVMzyOf5q8oX',
            '_nb_ioWEgULi': '',
            'lsId': 'f3e9184bbb4f40539702a58ec91a587a',
        }

        headers = {
            'accept': 'application/json, text/plain, */*',
            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
            'cache-control': 'no-cache, no-store, must-revalidate',
            'content-type': 'application/json',
            'expires': '0',
            'jsec-x-df': '04facb30801ada1e5ac7e8e29a7a14ed3ed9f4d8d0d634be4167f0c3b8e0acd770e9835306f7557c2266e5f09cc238b5f730a9ea894a339fea3f5d30c5a581b1713d1dcc2f120fd08b53bff1ddcd0a8586fbd67569e7b8131154bd30d94ffcf4b29f9817748f50924b77e74992fa36f41a4150ba174639da7edb1e62c1e7c96e57fef81696c58bda62ffdd0f91',
            'origin': 'https://passport.jlc.com',
            'pragma': 'no-cache',
            'priority': 'u=1, i',
            'referer': 'https://passport.jlc.com/window/login?appId=JLC_PORTAL_PC&redirectUrl=https%3A%2F%2Fwww.jlc.com%2F',
            'sec-ch-ua': '"Microsoft Edge";v="143", "Chromium";v="143", "Not A(Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'secretkey': '35616236663038352d643366382d343131662d396239622d366439643132653639373764',
            'support-cookie-samesite': 'true',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0',
            'x-jlc-clientinfo': 'eyJjbGllbnRUeXBlIjoiUEMtV0VCIiwib3NOYW1lIjoiV2luZG93cyIsIm9zVmVyc2lvbiI6IjEwIiwiYnJvd3Nlck5hbWUiOiJFZGdlIiwiYnJvd3NlclZlcnNpb24iOiIxNDMuMC4wLjAiLCJicm93c2VyRW5naW5lIjoiQmxpbmsiLCJicm93c2VyRW5naW5lVmVyc2lvbiI6IjE0My4wLjAuMCIsInNjcmVlbldpZHRoIjoxNzA3LCJzY3JlZW5IZWlnaHQiOjEwNjcsImRwciI6MS41LCJjb2xvckRlcHRoIjoyNCwicGl4ZWxEZXB0aCI6MjQsImdwdVZlbmRvciI6Ikdvb2dsZSBJbmMuIChOVklESUEpIiwiZ3B1UmVuZGVyZXIiOiJBTkdMRSAoTlZJRElBLCBOVklESUEgR2VGb3JjZSBSVFggNTA2MCBMYXB0b3AgR1BVICgweDAwMDAyRDU5KSBEaXJlY3QzRDExIHZzXzVfMCBwc181XzAsIEQzRDExKSIsImNwdUFyY2hpdGVjdHVyZSI6ImFtZDY0IiwiaGFyZHdhcmVDb25jdXJyZW5jeSI6MjQsImxhbmd1YWdlIjoiemgtQ04iLCJ0aW1lWm9uZSI6IkFzaWEvU2hhbmdoYWkiLCJ0aW1lem9uZU9mZnNldCI6LTQ4MCwibmV0VHlwZSI6IjRnIn0=',
            'x-jlc-clientuuid': '445de653-7a24-4242-88dd-0878479726aa-1766237894098',
            # 'cookie': 'JSESSIONID=; device_id=c7d0a5f4b554477fae0e1ba29f84fb63; HWWAFSESID=bcd7d8b4f625fb57ac; HWWAFSESTIME=1766299533105; Qs_lvt_290854=1766237893%2C1766299553; Qs_pv_290854=2499244294467079700%2C852781256760664000; __sameSiteCheck__=1; _c_WBKFRo=03ctatXDH7wXL1GIRpFWI9AUfuGhSVMzyOf5q8oX; _nb_ioWEgULi=; lsId=f3e9184bbb4f40539702a58ec91a587a',
        }

        json_data = {
            'username': username,
            'password': password,
            'isAutoLogin': True,
            'captchaTicket': self.captchaTicket,
        }

        response = requests.post('https://passport.jlc.com/api/cas/login/with-password', cookies=cookies,
                                 headers=headers, json=json_data)

        print(response.text)

    def test(self):
        # self.DeviceConfig = "dJu8EzQGjhxC8FYlpAabkxAHYnVQedbbQFlHNwXHRvrR7nvUgZLOwYTaZFdPkqDi41XQ7kG2YWG3DRpCS5Wu7XQomF/rdKV+n5EHU40IW3mw/J/CWpz4/iMWYskLCzRyxcEqJSVNigL16aqn6v2RvPnQBYXfDRu/BzEgKcRt51Naq28M9SNBDVkx20u1GJqRW4yeQHUxIcsfynDJ/a8+hMqZVmPlzoBs5arjg5T85ZNF7+03hgRZXBKCBMVP45QA"
        pass

    def main(self):
        # print('nowts', time.time())
        ali = AliV3()
        ali.Req_Init()
        # ali.test()
        ali.decrypt_DeviceConfig()
        ali.GetDynamic_Key()
        ali.GetLog2()
        ali.GetLog3()
        username = '10754308A'
        password = 'Aa123123'
        res = ali.Sumbit_All()
        enc_username = pwdEncrypt(username)
        enc_password = pwdEncrypt(password)
        ali.Login(enc_username, enc_password)
        return res
        # print('nowts', time.time())


if __name__ == '__main__':
    ali = AliV3()
    ali.main()
