import json
import time
import uuid
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

# ================= 配置区域 =================
GLOBAL_PUBLIC_KEY = "043b2759c70dab4718520cad55ac41eea6f8922c1309afb788f7578b3e585b167811023effefc2b9193cd93ae9c9a2a864e5fffbf7517c679f40cbf4c4630aa28c"
MAIN_URL = "https://www.jlc.com"
PASSPORT_URL = "https://passport.jlc.com/login?appId=JLC_PORTAL_PC"

def log(msg):
    """带时间戳的日志"""
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def init_driver():
    """初始化浏览器配置"""
    log("正在启动 Chrome 浏览器 (无头模式)...")
    chrome_options = Options()
    chrome_options.add_argument("--headless=new")
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    # 保持 User-Agent 一致性
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 防检测配置
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=chrome_options)
    # 屏蔽 webdriver 特征
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

def get_waf_cookies(driver):
    """
    执行特定的 WAF Cookie 获取流程：
    1. 访问主页
    2. 如果有 WAF Cookie -> 删除 -> 刷新
    3. 如果没有 -> 刷新 (最多3次)
    """
    log(f"正在访问主页: {MAIN_URL}")
    driver.get(MAIN_URL)
    time.sleep(2) # 等待初始加载

    waf_keys = ['HWWAFSESID', 'HWWAFSESTIME']
    
    # 检查是否存在
    cookies = {c['name']: c['value'] for c in driver.get_cookies()}
    has_waf = all(k in cookies for k in waf_keys)

    if has_waf:
        log("检测到已存在 WAF Cookie，执行【手动删除并刷新】流程...")
        driver.delete_cookie('HWWAFSESID')
        driver.delete_cookie('HWWAFSESTIME')
        time.sleep(1)
        log("Cookie 已删除，正在刷新页面...")
        driver.refresh()
    else:
        log("未检测到 WAF Cookie，执行【重试刷新】流程...")
        for i in range(3):
            log(f"尝试第 {i+1}/3 次刷新...")
            driver.refresh()
            time.sleep(3)
            cookies = {c['name']: c['value'] for c in driver.get_cookies()}
            if all(k in cookies for k in waf_keys):
                log("刷新后成功获取到 WAF Cookie！")
                break
    
    # 最终提取
    time.sleep(2) # 等待 Set-Cookie 生效
    final_cookies = {c['name']: c['value'] for c in driver.get_cookies()}
    
    waf_result = {}
    for k in waf_keys:
        val = final_cookies.get(k)
        if val:
            waf_result[k] = val
        else:
            log(f"警告: 流程结束后仍未获取到 {k}")
            
    if waf_result:
        log(f"成功提取 WAF Cookie: {waf_result}")
    
    return waf_result

def get_auth_params(driver):
    """
    跳转到 Passport 获取 secretkey 和计算签名
    """
    log(f"正在跳转至登录页: {PASSPORT_URL}")
    driver.get(PASSPORT_URL)
    
    # 等待握手接口完成
    log("等待握手接口及 JS 加载 (5秒)...")
    time.sleep(5)

    # 1. 获取 SecretKey
    secret_key = ""
    try:
        key_pair_str = driver.execute_script("return localStorage.getItem('keyPair');")
        if key_pair_str:
            key_pair = json.loads(key_pair_str)
            secret_key = key_pair.get('keyId', '')
            log(f"成功获取 SecretKey: {secret_key[:10]}...")
        else:
            log("错误: LocalStorage 中未找到 keyPair")
    except Exception as e:
        log(f"获取 SecretKey 异常: {e}")

    # 2. 计算 jsec-x-df
    jsec_val = ""
    client_uuid = ""
    try:
        timestamp = int(time.time() * 1000)
        client_uuid = f"{uuid.uuid4()}-{timestamp}"
        
        # 确保 SM2Utils 已加载
        is_loaded = driver.execute_script("return typeof window.SM2Utils !== 'undefined';")
        if not is_loaded:
            log("错误: SM2Utils 未加载，页面可能不完整")
        else:
            # 调用页面内置加密
            js_code = f"return window.SM2Utils.encs('{GLOBAL_PUBLIC_KEY}', '{client_uuid}', 1);"
            jsec_val = driver.execute_script(js_code)
            log("成功调用浏览器 SM2 加密生成签名")
    except Exception as e:
        log(f"JS 加密执行异常: {e}")

    return secret_key, client_uuid, jsec_val

def main():
    driver = init_driver()
    try:
        # 第一阶段：获取 WAF Cookie
        waf_cookies = get_waf_cookies(driver)
        
        if not waf_cookies:
            log("严重错误: 无法获取 WAF Cookie，程序终止")
            return

        # 第二阶段：获取登录加密参数
        secret_key, client_uuid, jsec_val = get_auth_params(driver)

        if not secret_key or not jsec_val:
            log("严重错误: 无法获取密钥或签名，程序终止")
            return

        # 获取所有 Cookie (包含 Passport 域名的 Session ID)
        all_selenium_cookies = driver.get_cookies()
        final_cookies = {}
        for c in all_selenium_cookies:
            final_cookies[c['name']] = c['value']
        
        # 确保 WAF Cookie 存在 (有时跳转域名可能会丢失，强制补全)
        final_cookies.update(waf_cookies)

        # 获取 UA
        user_agent = driver.execute_script("return navigator.userAgent;")

        # ================== 输出结果 ==================
        print("\n" + "="*20 + " 结果输出 " + "="*20)
        
        print("        cookies = {")
        # 输出 WAF Cookie
        for k in ['HWWAFSESID', 'HWWAFSESTIME']:
            if k in final_cookies:
                print(f"            '{k}': '{final_cookies[k]}',")
        
        # 输出其他关键 Cookie
        keys_to_show = ['device_id', 'Qs_lvt_290854', 'Qs_pv_290854', '__sameSiteCheck__', 'JSESSIONID']
        for k in final_cookies:
            if k not in ['HWWAFSESID', 'HWWAFSESTIME']: # 避免重复
                print(f"            '{k}': '{final_cookies[k]}',")
        print("        }")

        print("\n        headers = {")
        print(f"            'accept': 'application/json, text/plain, */*',")
        print(f"            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',")
        print(f"            'cache-control': 'no-cache, no-store, must-revalidate',")
        print(f"            'content-type': 'application/json',")
        print(f"            'origin': 'https://passport.jlc.com',")
        print(f"            'referer': '{PASSPORT_URL}',")
        print(f"            'user-agent': '{user_agent}',")
        print(f"            'secretkey': '{secret_key}',")
        print(f"            'x-jlc-clientuuid': '{client_uuid}',")
        print(f"            'jsec-x-df': '{jsec_val}',")
        # 这是一个固定的环境指纹，照抄即可
        print(f"            'x-jlc-clientinfo': 'eyJjbGllbnRUeXBlIjoiUEMtV0VCIn0=',")
        print("        }")

    except Exception as e:
        log(f"程序运行异常: {e}")
    finally:
        driver.quit()
        log("浏览器已关闭")

if __name__ == "__main__":
    main()
