import json
import time
import uuid
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.common.exceptions import WebDriverException

# ================= 配置区域 =================
# 全局固定公钥 (用于加密 jsec-x-df)
GLOBAL_PUBLIC_KEY = "043b2759c70dab4718520cad55ac41eea6f8922c1309afb788f7578b3e585b167811023effefc2b9193cd93ae9c9a2a864e5fffbf7517c679f40cbf4c4630aa28c"

# 目标登录页面 (访问此页面会自动触发握手和WAF Cookie下发)
TARGET_URL = "https://passport.jlc.com/login?appId=JLC_PORTAL_PC"

def log(msg):
    """格式化日志输出"""
    print(f"[{time.strftime('%H:%M:%S')}] {msg}")

def init_driver():
    """初始化 Selenium WebDriver (无头模式 + 防检测)"""
    log("正在启动 Chrome 浏览器 (无头模式)...")
    chrome_options = Options()
    
    # 基础无头配置
    chrome_options.add_argument("--headless=new")  # 新版无头模式，更像真实浏览器
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument("--disable-dev-shm-usage")
    
    # 关键：设置 User-Agent (必须与 headers 中的一致)
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
    
    # 屏蔽自动化特征
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    try:
        driver = webdriver.Chrome(options=chrome_options)
        # 进一步屏蔽 navigator.webdriver 特征
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": """
            Object.defineProperty(navigator, 'webdriver', {
              get: () => undefined
            })
            """
        })
        return driver
    except Exception as e:
        log(f"启动浏览器失败: {e}")
        sys.exit(1)

def main():
    driver = init_driver()
    
    try:
        # 1. 访问登录页，触发 WAF 和 secretKey 更新
        log(f"正在访问登录页面: {TARGET_URL}")
        driver.get(TARGET_URL)
        
        # 等待页面加载和 JS 执行 (握手接口是异步的)
        log("等待页面加载及后台握手请求 (5秒)...")
        time.sleep(5) 

        # 2. 从 LocalStorage 获取 secretKey
        # 嘉立创前端将 keyId 存储在 localStorage 的 'keyPair' 字段中
        log("正在提取 LocalStorage 中的密钥...")
        try:
            key_pair_str = driver.execute_script("return localStorage.getItem('keyPair');")
            if not key_pair_str:
                raise ValueError("LocalStorage 'keyPair' 为空，可能是握手请求被拦截或尚未完成")
            
            key_pair = json.loads(key_pair_str)
            secret_key = key_pair.get('keyId')
            if not secret_key:
                raise ValueError("无法从 keyPair 中找到 keyId")
                
            log(f"成功获取 SecretKey: {secret_key[:10]}...")
            
        except Exception as e:
            log(f"获取 SecretKey 失败: {e}")
            log("尝试通过 document.cookie 和 页面状态排查...")
            driver.quit()
            sys.exit(1)

        # 3. 构造 Client UUID
        timestamp = int(time.time() * 1000)
        client_uuid = f"{uuid.uuid4()}-{timestamp}"
        log(f"生成的 ClientUUID: {client_uuid}")

        # 4. 调用浏览器内部函数进行 SM2 加密
        # 直接使用页面上的 SM2Utils.encs 函数
        log("正在调用浏览器控制台 SM2Utils 进行加密...")
        try:
            # 这里的 1 代表 cipherMode C1C3C2，与你 JS 文件中一致
            js_code = f"return window.SM2Utils.encs('{GLOBAL_PUBLIC_KEY}', '{client_uuid}', 1);"
            jsec_x_df = driver.execute_script(js_code)
            
            if not jsec_x_df:
                raise ValueError("加密函数返回为空")
            
            log("加密成功，已生成 jsec-x-df 签名")
            
        except WebDriverException as e:
            log(f"调用 JS 加密失败: {e.msg}")
            log("可能原因: SM2Utils 对象未挂载到 window，页面可能加载不完全")
            driver.quit()
            sys.exit(1)

        # 5. 提取 Cookies
        log("正在提取浏览器 Cookies...")
        selenium_cookies = driver.get_cookies()
        final_cookies = {}
        
        # 将 Selenium cookie 列表转换为字典
        for cookie in selenium_cookies:
            final_cookies[cookie['name']] = cookie['value']

        # 确保 HWWAFSESID 存在 (如果没有，可能被风控)
        if 'HWWAFSESID' in final_cookies:
            log("检测到 HWWAF 防火墙 Cookie，提取成功")
        else:
            log("警告: 未检测到 HWWAFSESID，可能需要更换 IP 或稍后重试")

        # 6. 获取 User-Agent
        user_agent = driver.execute_script("return navigator.userAgent;")

        # ================== 输出结果 ==================
        print("\n" + "="*60)
        print("以下内容可直接复制到 with-password 请求代码中")
        print("="*60 + "\n")

        print("        cookies = {")
        for k, v in final_cookies.items():
            print(f"            '{k}': '{v}',")
        print("        }")
        
        print("\n        headers = {")
        print(f"            'accept': 'application/json, text/plain, */*',")
        print(f"            'accept-language': 'zh-CN,zh;q=0.9,en;q=0.8',")
        print(f"            'cache-control': 'no-cache, no-store, must-revalidate',")
        print(f"            'content-type': 'application/json',")
        print(f"            'origin': 'https://passport.jlc.com',")
        print(f"            'referer': '{TARGET_URL}',")
        print(f"            'user-agent': '{user_agent}',")
        print(f"            'secretkey': '{secret_key}',")
        print(f"            'x-jlc-clientuuid': '{client_uuid}',")
        # jsec-x-df 是加密后的 uuid
        print(f"            'jsec-x-df': '{jsec_x_df}',")
        # x-jlc-clientinfo 是固定的 Base64 (PC-WEB)，这里用 Selenium 里的值或者硬编码
        print(f"            'x-jlc-clientinfo': 'eyJjbGllbnRUeXBlIjoiUEMtV0VCIn0=',") 
        print("        }")

    except Exception as e:
        log(f"发生未预期的错误: {e}")
    finally:
        log("关闭浏览器...")
        driver.quit()

if __name__ == "__main__":
    main()
