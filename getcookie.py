import json
import time
import sys
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

# ================= 配置区域 =================
USERNAME = "13800138000"
PASSWORD = "YourPassword123!"
LOGIN_URL = "https://passport.jlc.com/window/login?appId=JLC_PORTAL_PC&redirectUrl=https%3A%2F%2Fwww.jlc.com%2F"

# 填入你逆向获取到的 deviceToken (必须是新的、未过期的)
MY_DEVICE_TOKEN = "1eec3445f84742f7a5f90d2a814ff7ce"

# 你的逆向数据包
MOCK_RESULT = {
    "captchaResult": True,
    "bizResult": True,
    "sceneId": "6mw4mrmg", 
    "certifyId": "IVnw86J9JV",
    "deviceToken": MY_DEVICE_TOKEN
}

def log(msg):
    sys.stderr.write(f"[{time.strftime('%H:%M:%S')}] {msg}\n")
    sys.stderr.flush()

def init_driver():
    chrome_options = Options()
    # 开启性能日志
    chrome_options.set_capability('goog:loggingPrefs', {'performance': 'ALL'})
    
    # 调试建议关闭无头模式，看效果
    # chrome_options.add_argument("--headless=new") 
    
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("--window-size=1920,1080")
    chrome_options.add_argument("--no-sandbox")
    chrome_options.add_argument('user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36 Edg/143.0.0.0')
    
    chrome_options.add_argument("--disable-blink-features=AutomationControlled")
    chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
    chrome_options.add_experimental_option('useAutomationExtension', False)

    driver = webdriver.Chrome(options=chrome_options)
    driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
        "source": "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
    })
    return driver

def format_output(final_cookies, final_headers):
    output = []
    output.append("cookies = {")
    for k, v in final_cookies.items():
        output.append(f"    '{k}': '{v}',")
    output.append("}")
    output.append("")
    output.append("headers = {")
    filter_headers = [':method', ':authority', ':scheme', ':path']
    for k, v in final_headers.items():
        if k not in filter_headers:
            output.append(f"    '{k}': '{v}',")
    output.append("}")
    return "\n".join(output)

def main():
    driver = init_driver()
    try:
        # =================================================================
        # 核心 Hook 注入：在页面加载前注入
        # 这次我们要劫持的是 initAliyunCaptcha，这是 JLC 调用的入口
        # =================================================================
        mock_data_json = json.dumps(MOCK_RESULT)
        
        hook_script = f"""
        console.log("%c>>> [Python Hook] 注入环境初始化...", "color: red; font-size: 20px");

        // 使用 defineProperty 劫持 window.initAliyunCaptcha
        // 这样无论 aliyun sdk 什么时候加载，我们都能抢先一步
        var _originalInit = undefined;
        
        Object.defineProperty(window, 'initAliyunCaptcha', {{
            get: function() {{
                return function(config, callback) {{
                    console.log("%c>>> [Hook] JLC 调用了 initAliyunCaptcha!", "color: green; font-weight: bold;", config);
                    
                    // 1. 保存 JLC 传入的配置（主要是为了拿到那个回调函数）
                    // 实际上 callback 经常在 config 里，但也可能作为第二个参数
                    window.__jlc_config = config;
                    
                    // 2. 返回一个伪造的验证码实例
                    // 这个实例必须有 show 方法，否则 JLC 代码会报错
                    return Promise.resolve({{
                        bind: function() {{}},
                        show: function() {{
                            console.log("%c>>> [Hook] JLC 尝试弹出滑块，已拦截！", "color: red; font-weight: bold;");
                            
                            var mockData = {mock_data_json};
                            
                            console.log(">>> [Hook] 准备执行回调，注入数据:", mockData);
                            
                            // 3. 执行 JLC 的回调函数
                            // JLC 的回调通常定义在 config.captchaVerifyCallback 或者 config.success
                            var verifyCallback = config.captchaVerifyCallback || config.success;
                            
                            if (verifyCallback) {{
                                // 模拟人类操作延迟
                                setTimeout(function() {{
                                    try {{
                                        // 调用回调：参数1是数据，参数2是 next 函数 (V3特有)
                                        verifyCallback.call(this, mockData, function(bizResult) {{
                                            console.log(">>> [Hook] JLC 业务层返回结果:", bizResult);
                                        }});
                                        console.log(">>> [Hook] 回调执行完毕！");
                                    }} catch(e) {{
                                        console.error(">>> [Hook] 回调执行出错:", e);
                                    }}
                                }}, 500);
                            }} else {{
                                console.error(">>> [Hook] 未找到回调函数！Config:", config);
                            }}
                        }},
                        reset: function() {{}}
                    }});
                }}
            }},
            set: function(val) {{
                // 忽略真实的 SDK 赋值，或者保存它
                console.log(">>> [Hook] 真实的 AliyunCaptcha 尝试加载，已被我们屏蔽。");
                _originalInit = val;
            }},
            configurable: true
        }});
        """
        
        driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
            "source": hook_script
        })
        
        log(f"1. 打开登录页: {LOGIN_URL}")
        driver.get(LOGIN_URL)
        
        # 页面加载后，检查是否 Hook 成功
        # 打开控制台应该能看到红色的 "[Python Hook] 注入环境初始化..."
        
        wait = WebDriverWait(driver, 10)
        
        log("2. 输入账号密码...")
        username_input = wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "input[type='text'], input[placeholder*='手机']")))
        password_input = driver.find_element(By.CSS_SELECTOR, "input[type='password']")
        
        username_input.clear()
        username_input.send_keys(USERNAME)
        time.sleep(0.5)
        password_input.clear()
        password_input.send_keys(PASSWORD)
        time.sleep(0.5)

        try:
            checkbox = driver.find_element(By.CSS_SELECTOR, ".el-checkbox__original")
            if not checkbox.selected:
                driver.execute_script("arguments[0].click();", checkbox)
        except:
            pass

        log("3. 点击登录...")
        # 此时 JLC 会调用 window.initAliyunCaptcha -> 我们的 Hook -> 返回假对象
        # 然后调用 假对象.show() -> 触发我们的回调 -> 发送 with-password
        login_btn = driver.find_element(By.CSS_SELECTOR, "button.el-button--primary")
        driver.execute_script("arguments[0].click();", login_btn)
        
        log("4. 等待捕获请求...")
        target_headers = None
        
        # 循环检测网络日志
        for i in range(20):
            logs = driver.get_log('performance')
            for entry in reversed(logs):
                try:
                    message = json.loads(entry['message'])['message']
                    if message['method'] == 'Network.requestWillBeSent':
                        params = message['params']
                        if '/with-password' in params['request']['url']:
                            log(">>> 成功捕获 with-password 请求！")
                            target_headers = params['request']['headers']
                            break
                except:
                    pass
            if target_headers:
                break
            time.sleep(0.5)

        if not target_headers:
            log("失败：未捕获到请求。请检查浏览器控制台是否有 Hook 报错。")
            # 调试时可以不退出，手动检查
            # input("按回车退出...") 
            return

        selenium_cookies = driver.get_cookies()
        final_cookies = {c['name']: c['value'] for c in selenium_cookies}

        print(format_output(final_cookies, target_headers))

    except Exception as e:
        log(f"Error: {e}")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
