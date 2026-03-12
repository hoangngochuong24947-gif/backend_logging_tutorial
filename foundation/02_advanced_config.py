"""
后端日志教学 - 基础层：高级日志配置
文件名：02_advanced_config.py
功能：学习更复杂的日志配置和管理技巧

教学目标：
1. 掌握多个logger的层次结构
2. 学习使用配置文件配置日志
3. 了解日志轮转和归档
4. 掌握多进程环境下的日志处理
"""

import logging
import logging.config
import logging.handlers
import os
import time

# ============================================
# 第一部分：logger的层次结构
# ============================================

print("=" * 50)
print("Logger的层次结构")
print("=" * 50)

# Python的logger采用层次结构，使用点号分隔
# 例如：'parent.child.grandchild'
# 子logger会继承父logger的配置

# 创建父logger
parent_logger = logging.getLogger('parent')
parent_logger.setLevel(logging.INFO)

# 创建控制台handler并添加到父logger
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
parent_logger.addHandler(console_handler)

# 创建子logger
child_logger = logging.getLogger('parent.child')
# 子logger没有显式设置level，会继承父logger的INFO级别
# 子logger没有添加handler，会使用父logger的handler

# 测试日志记录
print("\n测试层次结构的logger:")
parent_logger.info("父logger的信息")
child_logger.info("子logger的信息 - 使用父logger的配置")
child_logger.debug("子logger的调试信息 - 不会被记录，因为级别是INFO")

# ============================================
# 第二部分：使用配置文件配置日志
# ============================================

print("\n" + "=" * 50)
print("使用配置文件配置日志")
print("=" * 50)

# 定义日志配置字典
LOGGING_CONFIG = {
    'version': 1,  # 必须设置为1
    'disable_existing_loggers': False,  # 不禁用已有的logger

    # 定义formatters
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] - %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'detailed': {
            'format': '[%(levelname)s] %(asctime)s [%(filename)s:%(lineno)d] [%(funcName)s] - %(message)s'
        },
        'simple': {
            'format': '%(levelname)s: %(message)s'
        }
    },

    # 定义handlers
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'simple',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.FileHandler',
            'level': 'DEBUG',
            'formatter': 'standard',
            'filename': 'app_debug.log',
            'mode': 'w'  # 'w'表示覆盖，'a'表示追加
        },
        'error_file': {
            'class': 'logging.FileHandler',
            'level': 'ERROR',
            'formatter': 'detailed',
            'filename': 'app_error.log',
            'mode': 'a'
        }
    },

    # 定义loggers
    'loggers': {
        '': {  # 根logger
            'handlers': ['console'],
            'level': 'WARNING'
        },
        'app': {  # 应用主logger
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False  # 不向父logger传播
        },
        'app.database': {  # 数据库相关logger
            'handlers': ['file', 'error_file'],
            'level': 'INFO',
            'propagate': False
        }
    }
}

# 应用配置
logging.config.dictConfig(LOGGING_CONFIG)

print("\n使用配置文件的logger测试:")

# 获取配置好的logger
app_logger = logging.getLogger('app')
db_logger = logging.getLogger('app.database')
root_logger = logging.getLogger()  # 根logger

# 记录日志
app_logger.debug("App debug message")
app_logger.info("App info message")
app_logger.warning("App warning message")
db_logger.info("Database operation completed")
db_logger.error("Database connection failed")
root_logger.warning("Root warning message")

print("\n日志文件已创建:")
print("- app_debug.log: 包含所有DEBUG及以上级别的日志")
print("- app_error.log: 只包含ERROR及以上级别的日志")

# ============================================
# 第三部分：日志轮转和归档
# ============================================

print("\n" + "=" * 50)
print("日志轮转和归档")
print("=" * 50)

# 在生产环境中，日志文件可能会变得非常大
# 需要使用日志轮转来管理日志文件

def setup_rotating_log():
    """设置轮转日志"""

    # 创建轮转文件handler
    # 参数说明：
    # - filename: 日志文件名
    # - maxBytes: 单个日志文件最大大小（字节）
    # - backupCount: 保留的备份文件数量
    rotating_handler = logging.handlers.RotatingFileHandler(
        filename='rotating_app.log',
        maxBytes=1024,  # 1KB，仅用于演示
        backupCount=3,  # 保留3个备份文件
        encoding='utf-8'
    )

    rotating_handler.setLevel(logging.DEBUG)
    rotating_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(levelname)s - %(message)s'
    ))

    # 创建时间轮转handler
    # 每天创建一个新的日志文件
    timed_handler = logging.handlers.TimedRotatingFileHandler(
        filename='timed_app.log',
        when='midnight',  # 每天午夜轮转
        interval=1,  # 间隔1天
        backupCount=7,  # 保留7天的日志
        encoding='utf-8'
    )

    timed_handler.setLevel(logging.INFO)
    timed_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))

    # 创建logger并添加handlers
    rotating_logger = logging.getLogger('rotating')
    rotating_logger.setLevel(logging.DEBUG)
    rotating_logger.addHandler(rotating_handler)
    rotating_logger.addHandler(timed_handler)

    return rotating_logger

# 测试轮转日志
print("\n测试轮转日志（生成小文件以演示轮转）:")
rotating_logger = setup_rotating_log()

# 生成一些日志，使文件大小超过限制
for i in range(10):
    rotating_logger.info(f"测试轮转日志消息 {i}: {'x' * 100}")  # 每条消息100个字符

print("轮转日志已创建:")
print("- rotating_app.log: 当前日志文件")
print("- rotating_app.log.1, .2, .3: 备份文件")
print("- timed_app.log: 按时间轮转的日志文件")

# ============================================
# 第四部分：多进程环境下的日志处理
# ============================================

print("\n" + "=" * 50)
print("多进程环境下的日志处理")
print("=" * 50)

# 在多进程环境中，直接使用FileHandler可能导致日志混乱
# 需要使用QueueHandler和QueueListener

import multiprocessing
from logging.handlers import QueueHandler, QueueListener

def setup_queue_logging():
    """设置基于队列的日志系统"""

    # 创建队列
    log_queue = multiprocessing.Queue(-1)  # -1表示无限大小

    # 设置主进程的handler
    file_handler = logging.FileHandler('multiprocess.log')
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s [%(processName)s] %(levelname)s - %(message)s'
    ))

    # 创建QueueListener
    listener = QueueListener(log_queue, file_handler)
    listener.start()

    return log_queue, listener

def worker_process(log_queue, worker_id):
    """工作进程函数"""

    # 为工作进程设置QueueHandler
    queue_handler = QueueHandler(log_queue)
    queue_handler.setLevel(logging.DEBUG)

    # 获取logger
    logger = logging.getLogger(f'worker.{worker_id}')
    logger.setLevel(logging.DEBUG)
    logger.addHandler(queue_handler)

    # 记录一些日志
    logger.info(f"工作进程 {worker_id} 启动")
    logger.debug(f"工作进程 {worker_id} 处理数据")
    logger.warning(f"工作进程 {worker_id} 遇到警告")

    # 模拟工作
    time.sleep(0.1)

    logger.info(f"工作进程 {worker_id} 完成")

# 测试多进程日志
print("\n测试多进程日志处理:")
log_queue, listener = setup_queue_logging()

# 创建多个工作进程
processes = []
for i in range(3):
    p = multiprocessing.Process(
        target=worker_process,
        args=(log_queue, i),
        name=f'Worker-{i}'
    )
    processes.append(p)
    p.start()

# 等待所有进程完成
for p in processes:
    p.join()

# 停止listener
listener.stop()

print("多进程日志已保存到multiprocess.log文件中")

# ============================================
# 第五部分：实战练习 - 创建可配置的日志系统
# ============================================

print("\n" + "=" * 50)
print("实战练习：创建可配置的日志系统")
print("=" * 50)

class ConfigurableLogger:
    """可配置的日志系统类"""

    def __init__(self, config_path=None):
        """
        初始化日志系统

        Args:
            config_path: 配置文件路径，如果为None则使用默认配置
        """
        self.config_path = config_path
        self.setup_logging()

    def setup_logging(self):
        """设置日志系统"""
        if self.config_path and os.path.exists(self.config_path):
            # 从文件加载配置
            try:
                import yaml
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    config = yaml.safe_load(f)
                logging.config.dictConfig(config)
                print(f"从文件加载日志配置: {self.config_path}")
            except Exception as e:
                print(f"加载配置文件失败: {e}")
                self.setup_default_logging()
        else:
            # 使用默认配置
            self.setup_default_logging()

    def setup_default_logging(self):
        """设置默认日志配置"""
        default_config = {
            'version': 1,
            'formatters': {
                'default': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': 'INFO',
                    'formatter': 'default',
                    'stream': 'ext://sys.stdout'
                }
            },
            'loggers': {
                '': {
                    'handlers': ['console'],
                    'level': 'INFO'
                }
            }
        }

        logging.config.dictConfig(default_config)
        print("使用默认日志配置")

    def get_logger(self, name):
        """
        获取logger

        Args:
            name: logger名称

        Returns:
            logger对象
        """
        return logging.getLogger(name)

# 测试可配置的日志系统
print("\n测试ConfigurableLogger类:")

# 创建默认配置的logger
default_logger_system = ConfigurableLogger()
app_logger = default_logger_system.get_logger('myapp')
app_logger.info("使用默认配置的日志系统")

# ============================================
# 第六部分：知识点总结
# ============================================

print("\n" + "=" * 50)
print("知识点总结")
print("=" * 50)

summary = """
必须背下来的知识点：
1. logging.config.dictConfig() - 使用字典配置日志系统
2. logger层次结构：点号分隔，子logger继承父logger配置
3. RotatingFileHandler - 基于文件大小的日志轮转
4. QueueHandler/QueueListener - 多进程日志处理模式

需要熟悉掌握的知识点：
1. 日志配置字典的结构：version, formatters, handlers, loggers
2. TimedRotatingFileHandler - 基于时间的日志轮转
3. propagate属性：控制是否向父logger传播日志记录
4. 多环境下的日志配置：开发、测试、生产环境的不同配置

了解即可的知识点：
1. YAML/JSON配置文件的使用
2. 自定义Handler和Formatter的实现
3. 日志过滤器的使用
4. 日志性能优化技巧
"""

print(summary)

print("\n" + "=" * 50)
print("高级配置学习完成！")
print("下一步：学习日志与Web框架的集成")
print("=" * 50)