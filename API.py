from fastapi import FastAPI
import asyncio
import time
import uvicorn
from concurrent.futures import ThreadPoolExecutor

from AliV3 import AliV3

app = FastAPI()
executor = ThreadPoolExecutor(max_workers=3)


def blocking_task():
    """模拟阻塞的耗时任务"""
    print("开始执行耗时任务...")
    ali = AliV3()
    ali.Req_Init()
    # ali.test()
    ali.decrypt_DeviceConfig()
    ali.GetDynamic_Key()
    ali.GetLog2()
    ali.GetLog3()
    res = ali.Sumbit_All()
    return {
        "status": "completed",
        "message": "任务执行成功",
        "timestamp": res
    }


@app.get("/dj")
async def handle_dj():
    """处理 /dj 请求"""
    # 获取当前的事件循环
    loop = asyncio.get_event_loop()

    # 在线程池中执行阻塞任务
    result = await loop.run_in_executor(executor, blocking_task)

    return {
        "code": 200,
        "success": True,
        "data": result,
        "response_time": time.strftime("%Y-%m-%d %H:%M:%S")
    }


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=9999)
