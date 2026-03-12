# 后端日志基础速查表

## 日志级别速查

| 级别 | 数值 | 说明 | 使用场景 |
|------|------|------|----------|
| CRITICAL | 50 | 严重错误 | 系统崩溃、致命错误 |
| ERROR | 40 | 错误 | 操作失败、异常情况 |
| WARNING | 30 | 警告 | 潜在问题、异常但不影响功能 |
| INFO | 20 | 信息 | 正常操作记录、状态变更 |
| DEBUG | 10 | 调试 | 详细跟踪、变量值、流程信息 |
| NOTSET | 0 | 未设置 | 所有日志都记录 |

## 基本使用模式

### 1. 快速开始
```python
import logging

# 最简单的方式
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
logger.info("Hello World")
```

### 2. 标准配置
```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
```

### 3. 输出到文件
```python
import logging

logging.basicConfig(
    filename='app.log',
    filemode='a',  # 'a'追加，'w'覆盖
    level=logging.INFO,
    format='%(asctime)s - %(message)s'
)
```

## 格式字符串占位符

| 占位符 | 说明 | 示例 |
|--------|------|------|
| %(name)s | Logger名称 | `__main__`, `myapp.database` |
| %(levelname)s | 日志级别文本 | `INFO`, `ERROR`, `DEBUG` |
| %(asctime)s | 创建时间 | `2024-01-01 12:00:00` |
| %(message)s | 日志消息 | `User login successful` |
| %(filename)s | 文件名 | `app.py`, `models.py` |
| %(lineno)d | 行号 | `123`, `45` |
| %(funcName)s | 函数名 | `process_data`, `calculate` |
| %(module)s | 模块名 | `app`, `database.models` |
| %(pathname)s | 完整路径 | `/home/user/app/main.py` |
| %(process)d | 进程ID | `1234` |
| %(thread)d | 线程ID | `5678` |
| %(threadName)s | 线程名 | `MainThread`, `Thread-1` |

## 常用配置模式

### 开发环境配置
```python
# 开发环境：详细日志，输出到控制台
logging.basicConfig(
    level=logging.DEBUG,
    format='[%(levelname)s] %(name)s:%(lineno)d - %(message)s'
)
```

### 生产环境配置
```python
# 生产环境：重要日志，输出到文件
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    handlers=[
        logging.FileHandler('app_prod.log'),
        logging.StreamHandler()  # 可选：同时输出到控制台
    ]
)
```

### 字典配置（推荐）
```python
import logging.config

LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        }
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard'
        }
    },
    'loggers': {
        '': {  # 根logger
            'handlers': ['console'],
            'level': 'WARNING'
        },
        'myapp': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False
        }
    }
}

logging.config.dictConfig(LOGGING_CONFIG)
```

## 异常日志记录

### 1. 基本异常记录
```python
try:
    # 可能出错的代码
    result = 1 / 0
except Exception as e:
    logger.error("计算失败", exc_info=True)
```

### 2. 使用exception方法（自动记录堆栈）
```python
try:
    result = risky_operation()
except Exception:
    logger.exception("操作失败")  # 自动记录完整堆栈
```

### 3. 手动记录堆栈
```python
import traceback

try:
    result = risky_operation()
except Exception as e:
    logger.error(f"操作失败: {e}")
    logger.error(f"堆栈信息:\n{traceback.format_exc()}")
```

## Logger层次结构

### 创建层次化logger
```python
# 父logger
parent_logger = logging.getLogger('app')
parent_logger.setLevel(logging.INFO)

# 子logger（继承父logger配置）
child_logger = logging.getLogger('app.database')
# child_logger会自动使用父logger的配置

# 孙logger
grandchild_logger = logging.getLogger('app.database.queries')
```

### 控制传播行为
```python
# 阻止向父logger传播
logger = logging.getLogger('myapp')
logger.propagate = False  # 不再向父logger传播日志记录
```

## 常用Handler类型

| Handler类 | 说明 | 使用场景 |
|-----------|------|----------|
| StreamHandler | 输出到流（控制台） | 开发环境调试 |
| FileHandler | 输出到文件 | 生产环境日志记录 |
| RotatingFileHandler | 轮转文件（按大小） | 防止日志文件过大 |
| TimedRotatingFileHandler | 轮转文件（按时间） | 按天/周/月归档日志 |
| SocketHandler | 输出到网络socket | 远程日志收集 |
| HTTPHandler | 输出到HTTP服务器 | 发送到日志服务API |
| SMTPHandler | 通过邮件发送 | 错误告警邮件 |
| QueueHandler | 输出到队列 | 多进程日志处理 |

### 示例：轮转日志
```python
from logging.handlers import RotatingFileHandler

handler = RotatingFileHandler(
    filename='app.log',
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,  # 保留5个备份
    encoding='utf-8'
)
```

## 性能优化提示

### 1. 避免字符串拼接
```python
# 不好：总是执行字符串拼接
logger.debug(f"用户 {user_id} 的数据: {expensive_operation()}")

# 好：只在需要时执行
if logger.isEnabledFor(logging.DEBUG):
    logger.debug(f"用户 {user_id} 的数据: {expensive_operation()}")
```

### 2. 使用延迟求值
```python
# 使用%格式化和延迟参数
logger.debug("用户 %s 的数据: %s", user_id, expensive_operation())
```

### 3. 合理设置日志级别
```python
# 生产环境：较高级别
logger.setLevel(logging.INFO)

# 开发环境：较低级别
logger.setLevel(logging.DEBUG)

# 特定模块：自定义级别
database_logger = logging.getLogger('app.database')
database_logger.setLevel(logging.WARNING)  # 只记录警告和错误
```

## 常见问题解决

### 1. 日志不输出
- 检查logger级别设置
- 确认已添加handler
- 检查propagate设置（如果使用层次结构）

### 2. 中文乱码
```python
# 设置文件编码
handler = logging.FileHandler('app.log', encoding='utf-8')
```

### 3. 多进程日志混乱
```python
from logging.handlers import QueueHandler, QueueListener
import multiprocessing

# 使用QueueHandler处理多进程日志
log_queue = multiprocessing.Queue(-1)
queue_handler = QueueHandler(log_queue)
```

### 4. 日志文件权限问题
- 确保程序有写权限
- 检查磁盘空间
- 考虑使用/tmp目录或用户目录

## 最佳实践总结

### 必须遵守的规则
1. **不要使用print()** - 总是使用logging模块
2. **记录异常堆栈** - 使用`exc_info=True`或`logger.exception()`
3. **合理分级** - 根据消息重要性选择合适的级别
4. **包含上下文** - 在日志消息中包含相关标识符（用户ID、请求ID等）

### 推荐做法
1. **使用配置字典** - 而不是basicConfig()
2. **层次化logger** - 按模块组织logger
3. **分离日志类型** - 不同级别的日志输出到不同文件
4. **定期轮转** - 防止日志文件过大

### 高级技巧
1. **结构化日志** - 输出JSON格式日志，便于分析
2. **异步日志** - 在高并发场景下使用异步handler
3. **日志采样** - 对DEBUG日志进行采样，减少性能影响
4. **动态级别调整** - 运行时动态调整日志级别

## 快速参考命令

### 查看日志文件
```bash
# 查看最新日志
tail -f app.log

# 查看错误日志
grep "ERROR" app.log

# 查看特定时间段的日志
grep "2024-01-01" app.log

# 统计错误数量
grep -c "ERROR" app.log
```

### 日志文件管理
```bash
# 压缩旧日志
gzip app.log.1

# 清理过期日志
find /var/log -name "*.log.*" -mtime +30 -delete

# 按大小排序日志文件
ls -lhS *.log
```

---

## 下一步学习

1. **完成基础层练习** - 运行`01_basic_logging.py`等示例
2. **创建自己的日志配置** - 根据项目需求调整
3. **学习联合层** - 日志与Web框架集成
4. **探索高级功能** - 日志聚合和分析工具

记住：好的日志系统是调试和监控的基础，值得花时间精心设计。