import requests
import execjs
import time
import uuid
import random
import json

# ================= 配置 =================
JS_FILE_NAME = 'sm2.js'
GLOBAL_PUBLIC_KEY = "043b2759c70dab4718520cad55ac41eea6f8922c1309afb788f7578b3e585b167811023effefc2b9193cd93ae9c9a2a864e5fffbf7517c679f40cbf4c4630aa28c"

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
    
    # 1. 准备基础 Headers (修正为统一的 Windows 环境特征)
    base_headers = {
        'Accept': 'application/json, text/plain, */*',
        'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
        'Content-Type': 'application/json;charset=UTF-8',
        'Origin': 'https://passport.jlc.com',
        'Referer': 'https://passport.jlc.com/window/login?appId=JLC_PORTAL_PC&redirectUrl=https%3A%2F%2Fwww.jlc.com%2F',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
        'sec-ch-ua-mobile': '?0',
        'sec-ch-ua-platform': '"Windows"',  # 必须与 User-Agent 对应的系统一致
        'X-Requested-With': 'XMLHttpRequest'
    }
    
    # 2. 生成 Client UUID
    timestamp = int(time.time() * 1000)
    client_uuid = f"{uuid.uuid4()}-{timestamp}"
    
    # 3. 发送握手请求 (获取 secretkey 和 HWWAF Cookies)
    try:
        url = 'https://passport.jlc.com/api/cas-auth/secret/update'
        
        # 注意：不要在第一次请求时手动注入 fake_cookies，这可能导致服务端解析错误或指纹冲突。
        # 让 requests 自动处理服务器返回的 Set-Cookie。
        
        resp = session.post(url, headers=base_headers, json={}, timeout=15)
        
        if resp.status_code != 200:
            print(f"请求失败: {resp.status_code}")
            print(f"响应内容: {resp.text}") # 打印详细错误信息
            return

        resp_json = resp.json()
        secret_key = resp_json.get('data', {}).get('keyId')
        
        if not secret_key:
            print(f"未能获取 secretkey, 响应数据: {resp_json}")
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
    final_headers['x-jlc-clientinfo'] = 'eyJjbGllbnRUeXBlIjoiUEMtV0VCIn0=' 

    # 6. 提取最终 Cookies
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
