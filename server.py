from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import os
import subprocess

app = FastAPI(title="后端日志教学平台 API")

# 挂载前端模板目录
# 若目录不存在则创建它防止报错（这里默认是由上方的 write_to_file 写入）
current_dir = os.path.dirname(os.path.abspath(__file__))
frontend_path = os.path.join(current_dir, "frontend")
if not os.path.exists(frontend_path):
    os.makedirs(frontend_path, exist_ok=True)

templates = Jinja2Templates(directory="frontend")

# 默认读取在根目录下生成的日志文件
LOG_FILE_PATH = "app.log"

@app.get("/", response_class=HTMLResponse)
async def serve_index(request: Request):
    """渲染主页"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/api/logs")
async def get_logs():
    """实时读取日志文件并返回内容给前端大屏展示"""
    if not os.path.exists(LOG_FILE_PATH):
        return {"logs": "系统提示：该项目目录下目前没有生成 app.log 文件。点击左侧按钮来触发代码并生成日志吧！"}
    
    try:
        with open(LOG_FILE_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        return {"logs": content}
    except Exception as e:
        return {"logs": f"读取失败，请检查权限: {e}"}

@app.post("/api/trigger_basic")
async def trigger_basic():
    """执行基础知识的日志脚本，展示其向普通文件里写入数据"""
    try:
        # 子进程调用 foundation 下的基础教育代码
        target_script = os.path.join("foundation", "01_basic_logging.py")
        if not os.path.exists(target_script):
            return {"status": "error", "message": f"未找到文件 {target_script}，请确定挂载目录正确"}
            
        subprocess.run(["python", target_script], check=True, capture_output=True, text=True)
        return {"status": "success", "message": "已成功执行 01_basic_logging.py"}
    except subprocess.CalledProcessError as e:
        return {"status": "error", "message": f"脚本运行报错日志: {e.stderr}"}
    except Exception as e:
        return {"status": "error", "message": f"服务器内部错误: {e}"}

@app.post("/api/trigger_error")
async def trigger_error():
    """执行带有异常崩溃抓取的基础脚本"""
    try:
        target_script = os.path.join("foundation", "03_error_handling.py")
        if not os.path.exists(target_script):
            return {"status": "error", "message": f"未找到文件 {target_script}，请确定挂载目录正确"}
            
        # 这里之所以也判断成功，是因为虽然代码里故意抛出异常记录日志，但这恰恰是学习目的。程序本身是被 try-catch 或用特定捕获完成的。
        subprocess.run(["python", target_script], capture_output=True, text=True)
        return {"status": "success", "message": "已成功触发并隔离了一次 Exception，可见日志中的 traceback 追加"}
    except Exception as e:
        return {"status": "error", "message": f"执行失败: {e}"}

@app.post("/api/clear_logs")
async def clear_logs():
    """一键清理磁盘文件中的日志，让学生从零开始读新日志"""
    try:
        if os.path.exists(LOG_FILE_PATH):
            os.remove(LOG_FILE_PATH)
            return {"status": "success", "message": "本地磁盘的历史 app.log 文件已物理删除清空"}
        return {"status": "success", "message": "早已打扫干净，没有发现旧的日志文件"}
    except Exception as e:
        return {"status": "error", "message": f"删除文件失败，大概率是被进程占用中: {e}"}

if __name__ == "__main__":
    import uvicorn
    # 只要在这个项目下运行服务器，均可通过 8000 端口访问
    uvicorn.run(app, host="0.0.0.0", port=8000)
