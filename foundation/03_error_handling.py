"""
后端日志教学 - 基础层：错误处理和异常日志
文件名：03_error_handling.py
功能：学习如何在错误处理中使用日志，记录异常信息

教学目标：
1. 掌握异常日志记录的最佳实践
2. 学习记录完整的异常堆栈信息
3. 了解如何创建自定义异常类并记录日志
4. 掌握错误恢复和日志审计
"""

import logging
import traceback
import sys

# ============================================
# 第一部分：基础错误处理与日志记录
# ============================================

print("=" * 50)
print("基础错误处理与日志记录")
print("=" * 50)

# 配置基础日志
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def divide_numbers(a, b):
    """
    除法函数，演示基础错误处理

    Args:
        a: 被除数
        b: 除数

    Returns:
        除法结果

    Raises:
        ValueError: 当除数为0时
    """
    logger.info(f"开始计算除法: {a} / {b}")

    if b == 0:
        # 错误方式：只记录错误消息，没有异常信息
        logger.error("除数不能为0")
        raise ValueError("除数不能为0")

    try:
        result = a / b
        logger.info(f"计算完成: {a} / {b} = {result}")
        return result
    except Exception as e:
        # 错误方式：只记录异常对象，没有堆栈信息
        logger.error(f"除法计算错误: {e}")
        raise

print("\n测试基础错误处理:")
try:
    result1 = divide_numbers(10, 2)
    print(f"10 / 2 = {result1}")

    result2 = divide_numbers(10, 0)
    print(f"10 / 0 = {result2}")
except Exception as e:
    print(f"捕获到异常: {e}")

# ============================================
# 第二部分：记录完整的异常堆栈信息
# ============================================

print("\n" + "=" * 50)
print("记录完整的异常堆栈信息")
print("=" * 50)

def read_file_with_stacktrace(filename):
    """
    读取文件并记录完整的异常堆栈

    Args:
        filename: 文件名

    Returns:
        文件内容
    """
    logger = logging.getLogger('file_reader')

    logger.info(f"尝试读取文件: {filename}")

    try:
        with open(filename, 'r', encoding='utf-8') as f:
            content = f.read()
            logger.info(f"成功读取文件，长度: {len(content)} 字符")
            return content
    except FileNotFoundError as e:
        # 方式1：使用logger.exception()自动记录堆栈
        logger.exception(f"文件不存在: {filename}")
        raise
    except UnicodeDecodeError as e:
        # 方式2：手动记录堆栈信息
        logger.error(f"文件编码错误: {filename}")
        logger.error(f"错误详情: {e}")
        logger.error(f"堆栈信息:\n{traceback.format_exc()}")
        raise
    except Exception as e:
        # 方式3：使用exc_info参数
        logger.error(f"读取文件时发生未知错误: {filename}", exc_info=True)
        raise

print("\n测试异常堆栈记录:")
try:
    # 测试文件不存在的情况
    read_file_with_stacktrace("nonexistent_file.txt")
except Exception as e:
    print(f"预期中的异常: {type(e).__name__}")

# ============================================
# 第三部分：自定义异常类与日志记录
# ============================================

print("\n" + "=" * 50)
print("自定义异常类与日志记录")
print("=" * 50)

class ApplicationError(Exception):
    """应用基础异常类"""

    def __init__(self, message, error_code=None, context=None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}

    def log_error(self, logger):
        """记录异常日志"""
        logger.error(f"[{self.error_code}] {self.message}")
        if self.context:
            logger.error(f"上下文信息: {self.context}")

class DatabaseError(ApplicationError):
    """数据库异常"""

    def __init__(self, message, query=None, params=None):
        super().__init__(message, error_code="DB_ERROR")
        self.query = query
        self.params = params
        self.context = {
            'query': query,
            'params': params
        }

    def log_error(self, logger):
        """记录数据库异常日志"""
        super().log_error(logger)
        if self.query:
            logger.debug(f"查询语句: {self.query}")
        if self.params:
            logger.debug(f"查询参数: {self.params}")

class ValidationError(ApplicationError):
    """数据验证异常"""

    def __init__(self, message, field=None, value=None):
        super().__init__(message, error_code="VALIDATION_ERROR")
        self.field = field
        self.value = value
        self.context = {
            'field': field,
            'value': value
        }

# 测试自定义异常
print("\n测试自定义异常类:")

def process_user_data(user_data):
    """处理用户数据，演示自定义异常的使用"""

    logger = logging.getLogger('user_processor')

    logger.info(f"开始处理用户数据: {user_data}")

    # 数据验证
    if 'name' not in user_data:
        error = ValidationError("用户姓名不能为空", field='name')
        error.log_error(logger)
        raise error

    if 'age' not in user_data:
        error = ValidationError("用户年龄不能为空", field='age')
        error.log_error(logger)
        raise error

    try:
        age = int(user_data['age'])
        if age < 0 or age > 150:
            error = ValidationError("年龄必须在0-150之间", field='age', value=age)
            error.log_error(logger)
            raise error
    except ValueError as e:
        error = ValidationError("年龄必须是有效数字", field='age', value=user_data['age'])
        error.log_error(logger)
        raise error from e

    # 模拟数据库操作
    logger.info("数据验证通过，开始数据库操作")

    try:
        # 模拟数据库错误
        raise ConnectionError("数据库连接失败")
    except ConnectionError as e:
        db_error = DatabaseError(
            "无法连接数据库",
            query="INSERT INTO users VALUES (%s, %s)",
            params=(user_data['name'], user_data['age'])
        )
        db_error.log_error(logger)
        raise db_error from e

    logger.info("用户数据处理完成")

# 测试各种情况
test_cases = [
    {},  # 缺少所有字段
    {'name': '张三'},  # 缺少年龄
    {'name': '李四', 'age': 'invalid'},  # 无效年龄
    {'name': '王五', 'age': '200'},  # 年龄超出范围
    {'name': '赵六', 'age': '25'},  # 应该触发数据库错误
]

for i, user_data in enumerate(test_cases, 1):
    print(f"\n测试用例 {i}: {user_data}")
    try:
        process_user_data(user_data)
        print("处理成功")
    except ApplicationError as e:
        print(f"捕获到应用异常: {type(e).__name__} - {e.message}")
    except Exception as e:
        print(f"捕获到其他异常: {type(e).__name__} - {e}")

# ============================================
# 第四部分：错误恢复与日志审计
# ============================================

print("\n" + "=" * 50)
print("错误恢复与日志审计")
print("=" * 50)

class ResilientSystem:
    """具有错误恢复能力的系统"""

    def __init__(self):
        self.logger = logging.getLogger('resilient.system')
        self.error_count = 0
        self.max_retries = 3
        self.recovery_logger = self._setup_recovery_logger()

    def _setup_recovery_logger(self):
        """设置恢复日志记录器"""
        recovery_logger = logging.getLogger('recovery.audit')

        # 创建审计日志文件handler
        audit_handler = logging.FileHandler('recovery_audit.log')
        audit_handler.setLevel(logging.INFO)
        audit_handler.setFormatter(logging.Formatter(
            '%(asctime)s [AUDIT] %(levelname)s - %(message)s'
        ))

        recovery_logger.addHandler(audit_handler)
        recovery_logger.setLevel(logging.INFO)

        return recovery_logger

    def perform_operation(self, operation_id):
        """
        执行操作，具有重试机制

        Args:
            operation_id: 操作ID
        """
        self.logger.info(f"开始执行操作: {operation_id}")

        for attempt in range(1, self.max_retries + 1):
            try:
                # 模拟可能失败的操作
                if attempt < self.max_retries and operation_id % 3 == 0:
                    raise RuntimeError(f"操作 {operation_id} 模拟失败")

                # 操作成功
                self.logger.info(f"操作 {operation_id} 执行成功 (尝试 {attempt})")
                self.recovery_logger.info(f"操作成功: {operation_id}, 尝试次数: {attempt}")

                # 重置错误计数
                if self.error_count > 0:
                    self.logger.warning(f"错误计数已重置: {self.error_count} -> 0")
                    self.error_count = 0

                return True

            except Exception as e:
                self.error_count += 1
                self.logger.warning(f"操作 {operation_id} 尝试 {attempt} 失败: {e}")

                # 记录审计日志
                self.recovery_logger.warning(
                    f"操作失败: {operation_id}, "
                    f"尝试: {attempt}, "
                    f"错误: {type(e).__name__}, "
                    f"累计错误: {self.error_count}"
                )

                if attempt < self.max_retries:
                    # 等待重试
                    wait_time = attempt * 2  # 退避策略
                    self.logger.info(f"等待 {wait_time} 秒后重试...")
                    import time
                    time.sleep(0.1)  # 缩短等待时间用于演示
                else:
                    # 所有重试都失败
                    self.logger.error(f"操作 {operation_id} 所有重试均失败")
                    self.recovery_logger.error(
                        f"操作最终失败: {operation_id}, "
                        f"总尝试次数: {attempt}, "
                        f"最后错误: {e}"
                    )

        return False

    def get_system_status(self):
        """获取系统状态"""
        status = {
            'error_count': self.error_count,
            'max_retries': self.max_retries,
            'status': 'healthy' if self.error_count < 5 else 'degraded'
        }

        self.logger.info(f"系统状态: {status}")
        return status

# 测试错误恢复系统
print("\n测试错误恢复系统:")

system = ResilientSystem()

# 执行多个操作
for op_id in range(1, 11):
    success = system.perform_operation(op_id)
    print(f"操作 {op_id}: {'成功' if success else '失败'}")

# 检查系统状态
status = system.get_system_status()
print(f"\n最终系统状态: {status}")

print("\n审计日志已保存到recovery_audit.log文件")

# ============================================
# 第五部分：全局异常处理与日志记录
# ============================================

print("\n" + "=" * 50)
print("全局异常处理与日志记录")
print("=" * 50)

def setup_global_exception_handler():
    """设置全局异常处理器"""

    logger = logging.getLogger('global.exception')

    def global_exception_handler(exc_type, exc_value, exc_traceback):
        """
        全局异常处理函数

        Args:
            exc_type: 异常类型
            exc_value: 异常值
            exc_traceback: 异常堆栈
        """
        # 忽略KeyboardInterrupt，让控制台正确处理Ctrl+C
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        # 记录未捕获的异常
        logger.critical(
            "未捕获的异常",
            exc_info=(exc_type, exc_value, exc_traceback)
        )

        # 还可以执行其他操作，如发送警报、清理资源等
        print("\n⚠️  严重错误发生！详细信息已记录到日志。")

        # 调用默认的异常处理器
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    # 设置全局异常处理器
    sys.excepthook = global_exception_handler

    return logger

# 测试全局异常处理器
print("\n测试全局异常处理器:")

# 配置专门的异常日志
exception_logger = setup_global_exception_handler()

def function_that_crashes():
    """会崩溃的函数"""
    logger = logging.getLogger('crash_test')
    logger.info("准备执行会崩溃的操作...")

    # 这会导致未捕获的异常
    result = 1 / 0
    return result

print("即将触发未捕获的异常...")
print("注意：异常会被全局处理器捕获并记录")

# 在实际应用中，未捕获的异常会导致程序终止
# 这里我们使用try-except来防止程序真正崩溃
try:
    function_that_crashes()
except Exception as e:
    print(f"已捕获异常: {e}")

# ============================================
# 第六部分：实战练习 - 创建健壮的错误处理系统
# ============================================

print("\n" + "=" * 50)
print("实战练习：创建健壮的错误处理系统")
print("=" * 50)

class RobustAPIClient:
    """健壮的API客户端"""

    def __init__(self, base_url, max_retries=3):
        self.base_url = base_url
        self.max_retries = max_retries
        self.logger = logging.getLogger('api.client')
        self.stats_logger = logging.getLogger('api.stats')

        # 设置统计日志
        stats_handler = logging.FileHandler('api_stats.log')
        stats_handler.setFormatter(logging.Formatter(
            '%(asctime)s [STATS] %(message)s'
        ))
        self.stats_logger.addHandler(stats_handler)

    def make_request(self, endpoint, method='GET', data=None):
        """
        发送API请求，具有错误处理和重试机制

        Args:
            endpoint: API端点
            method: HTTP方法
            data: 请求数据

        Returns:
            响应数据

        Raises:
            APIConnectionError: 连接错误
            APIError: API错误
        """
        import random
        import time

        url = f"{self.base_url}/{endpoint}"
        self.logger.info(f"准备请求: {method} {url}")

        for attempt in range(1, self.max_retries + 1):
            try:
                # 模拟网络请求
                self.logger.debug(f"尝试 {attempt}: 发送请求到 {url}")

                # 模拟随机失败
                if random.random() < 0.3:  # 30%的失败率
                    raise ConnectionError(f"连接到 {url} 失败")

                if random.random() < 0.2:  # 20%的API错误率
                    raise ValueError(f"API返回错误: 无效数据")

                # 模拟成功响应
                response = {
                    'status': 'success',
                    'data': f'Response from {url}',
                    'attempt': attempt
                }

                self.logger.info(f"请求成功: {method} {url} (尝试 {attempt})")

                # 记录统计信息
                self.stats_logger.info(
                    f"成功: {method} {endpoint}, "
                    f"尝试次数: {attempt}, "
                    f"数据大小: {len(str(data) if data else 0)}"
                )

                return response

            except ConnectionError as e:
                self.logger.warning(f"连接错误 (尝试 {attempt}): {e}")

                if attempt < self.max_retries:
                    # 退避策略
                    backoff_time = attempt * 0.5
                    self.logger.info(f"等待 {backoff_time:.1f} 秒后重试...")
                    time.sleep(backoff_time)
                else:
                    self.logger.error(f"所有连接尝试均失败: {url}")
                    self.stats_logger.error(
                        f"连接失败: {method} {endpoint}, "
                        f"总尝试次数: {attempt}"
                    )
                    raise

            except Exception as e:
                self.logger.error(f"API错误 (尝试 {attempt}): {e}", exc_info=True)

                # 记录统计信息
                self.stats_logger.error(
                    f"API错误: {method} {endpoint}, "
                    f"尝试次数: {attempt}, "
                    f"错误类型: {type(e).__name__}"
                )

                # 不重试非连接错误
                raise

        # 不应该到达这里
        raise RuntimeError("Unexpected state in make_request")

# 测试健壮的API客户端
print("\n测试RobustAPIClient:")

client = RobustAPIClient("https://api.example.com", max_retries=2)

# 模拟多个请求
endpoints = ['users', 'products', 'orders', 'inventory']

for endpoint in endpoints:
    print(f"\n请求端点: {endpoint}")
    try:
        response = client.make_request(endpoint, method='GET')
        print(f"成功: {response['data']}")
    except ConnectionError as e:
        print(f"连接失败: {e}")
    except Exception as e:
        print(f"其他错误: {type(e).__name__} - {e}")

print("\nAPI统计信息已保存到api_stats.log文件")

# ============================================
# 第七部分：知识点总结
# ============================================

print("\n" + "=" * 50)
print("知识点总结")
print("=" * 50)

summary = """
必须背下来的知识点：
1. logger.exception() - 自动记录异常堆栈信息
2. exc_info=True参数 - 在log方法中记录异常信息
3. traceback.format_exc() - 获取格式化的堆栈跟踪信息
4. 自定义异常类 - 创建有意义的错误类型

需要熟悉掌握的知识点：
1. 异常链（raise ... from ...）- 保留原始异常信息
2. 错误恢复模式 - 重试机制和退避策略
3. 审计日志 - 记录关键操作和错误恢复过程
4. 全局异常处理器 - 捕获未处理的异常

了解即可的知识点：
1. sys.excepthook - 系统级异常处理
2. 错误分类和分级 - 根据严重程度处理不同错误
3. 监控和告警集成 - 将错误日志与监控系统集成
4. 性能影响分析 - 日志记录对性能的影响
"""

print(summary)

print("\n" + "=" * 50)
print("错误处理学习完成！")
print("下一步：学习日志与Web框架的集成")
print("=" * 50)