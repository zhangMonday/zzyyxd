import requests
import execjs
import time
import uuid
import random
import json

# ================= 配置 =================
JS_FILE_NAME = 'sm2.js'
GLOBAL_PUBLIC_KEY = "043b2759c70dab4718520cad55ac41eea6f8922c1309afb788f7578b3e585b167811023effefc2b9193cd93ae9c9a2a864e5fffbf7517c679f40cbf4c4630aa28c"

# 模拟的静态 Cookie (用于填充那些 JS 生成的统计 Cookie，让伪装更像浏览器)
def generate_fake_analytics_cookies():
    now = int(time.time())
    # 模拟百度统计 ID
    hm_lvt = f"{now},{now+10},{now+50},{now+100}" 
    # 模拟 Qs_lvt (最后访问时间)
    qs_lvt = f"{now}"
    return {
        'device_id': str(uuid.uuid4()).replace('-', ''),
        'Qs_lvt_290854': qs_lvt,
        'Qs_pv_290854': '2499244294467079700%2C852781256760664000', # 模拟 PV 统计
        '__sameSiteCheck__': '1',
        '_c_WBKFRo': '03ctatXDH7wXL1GIRpFWI9AUfuGhSVMzyOf5q8oX', # 这是一个指纹相关的，通常固定或很长
        '_nb_ioWEgULi': '',
        'Hm_lvt_bdc175618582350273cc82e8dd494d69': hm_lvt
    }

def get_jsec_signature(client_uuid):
    """加载 JS 并计算 jsec-x-df"""
    try:
        with open(JS_FILE_NAME, 'r', encoding='utf-8') as f:
            js_code = f.read()
        
        # 补全浏览器环境
        ctx = execjs.compile("""
            var window = this;
            var navigator = { appName: 'Netscape', appVersion: '5.0', userAgent: 'Mozilla/5.0' };
            var document = { createElement: function() { return { getContext: function() {} } } };
            """ + js_code)
        
        # 调用 sm2Encrypt(data, key, mode) 
        # mode 1 表示 C1C3C2
        signature = ctx.call('sm2Encrypt', client_uuid, GLOBAL_PUBLIC_KEY, 1)
        return signature
    except Exception as e:
        print(f"Error loading JS: {e}")
        return None

def main():
    session = requests.Session()
    
    # 1. 准备基础 Headers (模拟浏览器)
    base_headers = {
        'accept': 'application/json, text/plain, */*',
        'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8,en-GB;q=0.7,en-US;q=0.6',
        'content-type': 'application/json',
        'origin': 'https://passport.jlc.com',
        'referer': 'https://passport.jlc.com/window/login?appId=JLC_PORTAL_PC&redirectUrl=https%3A%2F%2Fwww.jlc.com%2F',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0',
        'sec-ch-ua': '"Chromium";v="127", "Not)A;Brand";v="99", "Microsoft Edge Simulate";v="127", "Lemur";v="127"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Linux"'
    }
    
    # 2. 生成 Client UUID
    timestamp = int(time.time() * 1000)
    client_uuid = f"{uuid.uuid4()}-{timestamp}"
    
    # 3. 发送握手请求 (获取 secretkey 和 HWWAF Cookies)
    #    这里不需要带复杂的 cookies，服务器会下发新的
    try:
        url = 'https://passport.jlc.com/api/cas-auth/secret/update'
        # 加上 fake cookies 让请求看起来更正常
        fake_cookies = generate_fake_analytics_cookies()
        session.cookies.update(fake_cookies)
        
        resp = session.post(url, headers=base_headers, json={}, timeout=10)
        
        if resp.status_code != 200:
            print(f"请求失败: {resp.status_code}")
            return

        resp_json = resp.json()
        secret_key = resp_json.get('data', {}).get('keyId')
        
        if not secret_key:
            print("未能获取 secretkey")
            return

    except Exception as e:
        print(f"网络请求异常: {e}")
        return

    # 4. 计算签名
    jsec_val = get_jsec_signature(client_uuid)
    
    # 5. 组装最终 Headers
    final_headers = base_headers.copy()
    final_headers['cache-control'] = 'no-cache, no-store, must-revalidate'
    final_headers['secretkey'] = secret_key
    final_headers['x-jlc-clientuuid'] = client_uuid
    final_headers['jsec-x-df'] = jsec_val
    # 这是一个固定的环境信息Base64，通常不校验内容，照抄即可
    final_headers['x-jlc-clientinfo'] = 'eyJjbGllbnRUeXBlIjoiUEMtV0VCIn0=' 

    # 6. 提取最终 Cookies (Requests Session 自动合并了服务器返回的 HWWAF Cookie 和我们自己造的统计 Cookie)
    final_cookies = session.cookies.get_dict()

    # ================= 严格格式化输出 =================
    print(f"""
        cookies = {{""")
    for k, v in final_cookies.items():
        print(f"            '{k}': '{v}',")
    print("""        }

        headers = {""")
    for k, v in final_headers.items():
        print(f"            '{k}': '{v}',")
    print("""        }""")

if __name__ == '__main__':
    main()
