"""
后端日志教学 - 联合层：日志与Web框架集成
文件名：01_web_framework_integration.py
功能：学习如何将日志系统集成到Web框架中（以FastAPI为例）

教学目标：
1. 掌握FastAPI中的日志配置
2. 学习记录HTTP请求/响应日志
3. 了解中间件中的日志记录
4. 掌握结构化日志在Web应用中的使用
"""

import logging
import logging.config
import time
from datetime import datetime
from typing import Dict, Any
import json

# 为了运行这个示例，需要先安装fastapi和uvicorn
# pip install fastapi uvicorn

print("=" * 80)
print("Web框架日志集成 - FastAPI示例")
print("=" * 80)

# ============================================
# 第一部分：FastAPI基础日志配置
# ============================================

print("\n" + "=" * 50)
print("第一部分：FastAPI基础日志配置")
print("=" * 50)

# FastAPI使用Uvicorn作为ASGI服务器，Uvicorn有自己的日志配置
# 我们需要配置Uvicorn的日志系统，并添加应用日志

# 创建FastAPI应用的日志配置
FASTAPI_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'json': {
            '()': 'logging.Formatter',  # 实际项目中可以使用自定义JSON formatter
            'format': '%(message)s'  # JSON格式的日志
        },
        'access': {
            'format': '%(asctime)s - %(client_addr)s - "%(request_line)s" %(status_code)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        }
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': 'fastapi_app.log',
            'level': 'DEBUG',
            'formatter': 'standard',
            'encoding': 'utf-8'
        },
        'access_file': {
            'class': 'logging.FileHandler',
            'filename': 'fastapi_access.log',
            'level': 'INFO',
            'formatter': 'access',
            'encoding': 'utf-8'
        },
        'error_file': {
            'class': 'logging.FileHandler',
            'filename': 'fastapi_error.log',
            'level': 'ERROR',
            'formatter': 'standard',
            'encoding': 'utf-8'
        }
    },

    'loggers': {
        '': {  # 根logger
            'handlers': ['console'],
            'level': 'WARNING'
        },
        'app': {  # 应用主logger
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False
        },
        'app.api': {  # API相关logger
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'uvicorn': {  # Uvicorn服务器日志
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False
        },
        'uvicorn.error': {  # Uvicorn错误日志
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False
        },
        'uvicorn.access': {  # 访问日志（单独文件）
            'handlers': ['access_file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

# 应用配置
logging.config.dictConfig(FASTAPI_LOGGING_CONFIG)

print("FastAPI日志配置已加载")
print("- 应用日志: fastapi_app.log")
print("- 访问日志: fastapi_access.log")
print("- 错误日志: fastapi_error.log")

# ============================================
# 第二部分：创建带日志的FastAPI应用
# ============================================

print("\n" + "=" * 50)
print("第二部分：创建带日志的FastAPI应用")
print("=" * 50)

try:
    from fastapi import FastAPI, Request, HTTPException, Depends
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import JSONResponse
    import uvicorn

    print("FastAPI模块导入成功")

except ImportError as e:
    print(f"需要安装FastAPI和Uvicorn: {e}")
    print("运行: pip install fastapi uvicorn")
    exit(1)

# 创建应用
app = FastAPI(
    title="日志教学API",
    description="演示Web框架中的日志集成",
    version="1.0.0"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 获取应用logger
app_logger = logging.getLogger('app')
api_logger = logging.getLogger('app.api')

# ============================================
# 第三部分：请求日志中间件
# ============================================

print("\n" + "=" * 50)
print("第三部分：请求日志中间件")
print("=" * 50)

@app.middleware("http")
async def log_requests(request: Request, call_next):
    """
    请求日志中间件
    记录每个HTTP请求的详细信息
    """
    # 生成请求ID
    import uuid
    request_id = str(uuid.uuid4())[:8]

    # 记录请求开始
    start_time = time.time()

    # 收集请求信息
    request_info = {
        'request_id': request_id,
        'method': request.method,
        'url': str(request.url),
        'client_ip': request.client.host if request.client else 'unknown',
        'user_agent': request.headers.get('user-agent', 'unknown'),
        'timestamp': datetime.now().isoformat()
    }

    # 记录请求
    app_logger.info(
        f"请求开始: {request_info['method']} {request_info['url']} "
        f"(ID: {request_id}, IP: {request_info['client_ip']})"
    )

    api_logger.debug(f"请求详细信息: {request_info}")

    # 将请求ID添加到请求状态
    request.state.request_id = request_id

    try:
        # 处理请求
        response = await call_next(request)

        # 计算处理时间
        process_time = time.time() - start_time

        # 记录响应
        response_info = {
            'request_id': request_id,
            'status_code': response.status_code,
            'process_time': f"{process_time:.3f}s",
            'timestamp': datetime.now().isoformat()
        }

        app_logger.info(
            f"请求完成: {request_info['method']} {request_info['url']} -> "
            f"{response.status_code} ({process_time:.3f}s)"
        )

        api_logger.debug(f"响应详细信息: {response_info}")

        # 添加自定义头部
        response.headers['X-Request-ID'] = request_id
        response.headers['X-Process-Time'] = f"{process_time:.3f}"

        return response

    except Exception as e:
        # 记录异常
        process_time = time.time() - start_time

        app_logger.error(
            f"请求失败: {request_info['method']} {request_info['url']} -> "
            f"异常: {type(e).__name__} ({process_time:.3f}s)",
            exc_info=True
        )

        # 重新抛出异常
        raise

# ============================================
# 第四部分：带日志记录的API端点
# ============================================

print("\n" + "=" * 50)
print("第四部分：带日志记录的API端点")
print("=" * 50)

@app.get("/")
async def root(request: Request):
    """
    根端点
    """
    request_id = getattr(request.state, 'request_id', 'unknown')

    app_logger.info(f"[{request_id}] 访问根端点")
    api_logger.debug(f"[{request_id}] 根端点被访问，headers: {dict(request.headers)}")

    return {
        "message": "欢迎来到日志教学API",
        "request_id": request_id,
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check(request: Request):
    """
    健康检查端点
    """
    request_id = getattr(request.state, 'request_id', 'unknown')

    app_logger.info(f"[{request_id}] 健康检查")

    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "request_id": request_id
    }

@app.get("/users/{user_id}")
async def get_user(user_id: int, request: Request):
    """
    获取用户信息
    """
    request_id = getattr(request.state, 'request_id', 'unknown')

    app_logger.info(f"[{request_id}] 获取用户信息 user_id={user_id}")

    # 模拟数据库查询
    api_logger.debug(f"[{request_id}] 模拟数据库查询 user_id={user_id}")

    # 模拟用户不存在的情况
    if user_id > 100:
        app_logger.warning(f"[{request_id}] 用户不存在 user_id={user_id}")
        raise HTTPException(status_code=404, detail="用户不存在")

    # 模拟错误情况
    if user_id < 0:
        app_logger.error(f"[{request_id}] 无效的用户ID user_id={user_id}")
        raise HTTPException(status_code=400, detail="用户ID必须为正数")

    # 返回模拟数据
    user_data = {
        "id": user_id,
        "name": f"用户{user_id}",
        "email": f"user{user_id}@example.com",
        "created_at": datetime.now().isoformat()
    }

    api_logger.debug(f"[{request_id}] 返回用户数据: {user_data}")

    return {
        "user": user_data,
        "request_id": request_id
    }

@app.post("/users")
async def create_user(request: Request):
    """
    创建用户
    """
    request_id = getattr(request.state, 'request_id', 'unknown')

    app_logger.info(f"[{request_id}] 创建用户")

    try:
        # 获取请求体
        data = await request.json()
        api_logger.debug(f"[{request_id}] 请求数据: {data}")

        # 验证数据
        if 'name' not in data:
            app_logger.warning(f"[{request_id}] 缺少必要字段: name")
            raise HTTPException(status_code=400, detail="缺少姓名字段")

        if 'email' not in data:
            app_logger.warning(f"[{request_id}] 缺少必要字段: email")
            raise HTTPException(status_code=400, detail="缺少邮箱字段")

        # 模拟用户创建
        user_id = 101  # 模拟新用户ID
        new_user = {
            "id": user_id,
            "name": data['name'],
            "email": data['email'],
            "created_at": datetime.now().isoformat()
        }

        app_logger.info(f"[{request_id}] 用户创建成功 user_id={user_id}")
        api_logger.debug(f"[{request_id}] 创建的用户数据: {new_user}")

        return {
            "message": "用户创建成功",
            "user": new_user,
            "request_id": request_id
        }

    except json.JSONDecodeError:
        app_logger.error(f"[{request_id}] 请求体不是有效的JSON")
        raise HTTPException(status_code=400, detail="无效的JSON数据")
    except Exception as e:
        app_logger.error(
            f"[{request_id}] 创建用户时发生未知错误",
            exc_info=True
        )
        raise HTTPException(status_code=500, detail="服务器内部错误")

@app.get("/error-test")
async def error_test(request: Request):
    """
    错误测试端点，用于演示错误日志
    """
    request_id = getattr(request.state, 'request_id', 'unknown')

    app_logger.info(f"[{request_id}] 错误测试端点被访问")

    # 模拟不同类型的错误

    # 1. 除以零错误
    if request.query_params.get('type') == 'zero':
        app_logger.warning(f"[{request_id}] 尝试触发除以零错误")
        try:
            result = 1 / 0
        except Exception as e:
            app_logger.error(f"[{request_id}] 除以零错误发生", exc_info=True)
            raise HTTPException(status_code=500, detail="除以零错误")

    # 2. 键错误
    elif request.query_params.get('type') == 'key':
        app_logger.warning(f"[{request_id}] 尝试触发键错误")
        try:
            data = {}
            value = data['nonexistent_key']
        except Exception as e:
            app_logger.error(f"[{request_id}] 键错误发生", exc_info=True)
            raise HTTPException(status_code=500, detail="键错误")

    # 3. 自定义业务错误
    elif request.query_params.get('type') == 'business':
        app_logger.warning(f"[{request_id}] 尝试触发业务逻辑错误")
        raise HTTPException(
            status_code=400,
            detail="业务逻辑错误：无效的操作"
        )

    # 默认：成功响应
    return {
        "message": "错误测试端点",
        "available_errors": ["zero", "key", "business"],
        "usage": "添加查询参数 ?type=error_type",
        "request_id": request_id
    }

# ============================================
# 第五部分：异常处理器
# ============================================

print("\n" + "=" * 50)
print("第五部分：异常处理器")
print("=" * 50)

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """
    HTTP异常处理器
    """
    request_id = getattr(request.state, 'request_id', 'unknown')

    # 根据状态码记录不同级别的日志
    if exc.status_code >= 500:
        app_logger.error(
            f"[{request_id}] 服务器错误 {exc.status_code}: {exc.detail}",
            extra={'status_code': exc.status_code}
        )
    elif exc.status_code >= 400:
        app_logger.warning(
            f"[{request_id}] 客户端错误 {exc.status_code}: {exc.detail}",
            extra={'status_code': exc.status_code}
        )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.detail,
            "status_code": exc.status_code,
            "request_id": request_id,
            "path": request.url.path
        }
    )

@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """
    通用异常处理器
    """
    request_id = getattr(request.state, 'request_id', 'unknown')

    app_logger.error(
        f"[{request_id}] 未处理的异常: {type(exc).__name__}",
        exc_info=True
    )

    return JSONResponse(
        status_code=500,
        content={
            "error": "服务器内部错误",
            "type": type(exc).__name__,
            "request_id": request_id,
            "path": request.url.path
        }
    )

# ============================================
# 第六部分：依赖注入中的日志
# ============================================

print("\n" + "=" * 50)
print("第六部分：依赖注入中的日志")
print("=" * 50)

def get_logger():
    """
    依赖项：获取请求特定的logger
    """
    def _get_logger(request: Request):
        request_id = getattr(request.state, 'request_id', 'unknown')

        # 创建请求特定的logger
        class RequestLogger:
            def __init__(self, request_id):
                self.request_id = request_id
                self.logger = logging.getLogger('app.request')

            def debug(self, message):
                self.logger.debug(f"[{self.request_id}] {message}")

            def info(self, message):
                self.logger.info(f"[{self.request_id}] {message}")

            def warning(self, message):
                self.logger.warning(f"[{self.request_id}] {message}")

            def error(self, message, exc_info=False):
                self.logger.error(
                    f"[{self.request_id}] {message}",
                    exc_info=exc_info
                )

        return RequestLogger(request_id)

    return _get_logger

@app.get("/admin")
async def admin_dashboard(
    request: Request,
    logger: Request = Depends(get_logger())
):
    """
    管理员仪表板，使用依赖注入的logger
    """
    logger.info("访问管理员仪表板")

    # 记录一些操作
    logger.debug("获取管理员数据")

    # 模拟安全检查
    user_agent = request.headers.get('user-agent', 'unknown')
    if 'admin' not in user_agent.lower():
        logger.warning(f"可疑的用户代理: {user_agent}")

    return {
        "message": "管理员仪表板",
        "features": ["用户管理", "日志查看", "系统监控"],
        "request_id": getattr(request.state, 'request_id', 'unknown')
    }

# ============================================
# 第七部分：运行和测试
# ============================================

print("\n" + "=" * 50)
print("第七部分：运行和测试说明")
print("=" * 50)

if __name__ == "__main__":
    print("\n要运行此FastAPI应用，请执行以下步骤：")
    print("\n1. 安装依赖：")
    print("   pip install fastapi uvicorn")

    print("\n2. 运行应用：")
    print("   uvicorn integration.01_web_framework_integration:app --reload")

    print("\n3. 访问以下端点进行测试：")
    print("   - http://localhost:8000/                 # 根端点")
    print("   - http://localhost:8000/health           # 健康检查")
    print("   - http://localhost:8000/users/1          # 获取用户")
    print("   - http://localhost:8000/users/999        # 用户不存在")
    print("   - http://localhost:8000/error-test       # 错误测试")
    print("   - http://localhost:8000/error-test?type=zero  # 除以零错误")
    print("   - http://localhost:8000/admin            # 管理员页面")

    print("\n4. 查看日志文件：")
    print("   - fastapi_app.log     # 应用日志")
    print("   - fastapi_access.log  # 访问日志")
    print("   - fastapi_error.log   # 错误日志")

    print("\n5. 使用curl测试POST请求：")
    print('   curl -X POST http://localhost:8000/users \\')
    print('        -H "Content-Type: application/json" \\')
    print('        -d \'{"name":"张三","email":"zhangsan@example.com"}\'')

    print("\n" + "=" * 80)
    print("Web框架集成学习完成！")
    print("=" * 80)

# ============================================
# 第八部分：知识点总结
# ============================================

print("\n" + "=" * 50)
print("知识点总结")
print("=" * 50)

summary = """
必须背下来的知识点：
1. FastAPI中间件中的日志记录 - 使用@app.middleware("http")
2. 请求ID跟踪 - 为每个请求生成唯一ID，便于追踪
3. 异常处理器中的日志记录 - 统一处理错误日志
4. Uvicorn日志配置 - 配置访问日志和错误日志

需要熟悉掌握的知识点：
1. 结构化日志在Web应用中的使用 - 包含请求ID、用户ID等上下文
2. 依赖注入获取logger - 在端点函数中使用依赖注入的logger
3. HTTP状态码与日志级别对应关系 - 400级记录警告，500级记录错误
4. 访问日志格式 - 记录客户端IP、请求方法、URL、状态码、处理时间

了解即可的知识点：
1. ASGI服务器日志配置 - Uvicorn、Hypercorn等服务器的日志配置
2. 分布式追踪集成 - 与OpenTelemetry等分布式追踪系统集成
3. 日志采样和限流 - 在高并发场景下控制日志量
4. 实时日志监控 - 将日志发送到ELK、Loki等监控系统
"""

print(summary)

print("\n" + "=" * 50)
print("下一步：学习日志与数据库的集成")
print("=" * 50)