"""
后端日志教学 - 基础层：Python标准库logging模块
文件名：01_basic_logging.py
功能：学习Python内置logging模块的基本使用方法

教学目标：
1. 理解日志级别及其重要性
2. 掌握基本的日志配置方法
3. 学会使用不同日志级别记录信息
4. 了解日志格式化和输出目标
"""

import logging

# ============================================
# 第一部分：日志级别介绍
# ============================================

print("=" * 50)
print("日志级别介绍")
print("=" * 50)

# Python logging模块定义了6个日志级别，从低到高分别是：
# 1. NOTSET (0): 不设置级别，所有日志都记录
# 2. DEBUG (10): 调试信息，用于开发阶段的详细跟踪
# 3. INFO (20): 一般信息，记录程序正常运行状态
# 4. WARNING (30): 警告信息，表示可能出现的问题
# 5. ERROR (40): 错误信息，记录程序运行中的错误
# 6. CRITICAL (50): 严重错误，可能导致程序崩溃

# 打印所有日志级别和对应的数值
print("\nPython日志级别及其数值：")
print(f"NOTSET:  {logging.NOTSET}")
print(f"DEBUG:   {logging.DEBUG}")
print(f"INFO:    {logging.INFO}")
print(f"WARNING: {logging.WARNING}")
print(f"ERROR:   {logging.ERROR}")
print(f"CRITICAL:{logging.CRITICAL}")

# ============================================
# 第二部分：最简单的日志使用方法
# ============================================

print("\n" + "=" * 50)
print("最简单的日志使用方法")
print("=" * 50)

# 使用basicConfig进行基本配置
# 这是最简单的日志配置方法，适合快速开始
logging.basicConfig(
    level=logging.DEBUG,  # 设置日志级别为DEBUG，记录所有DEBUG及以上级别的日志
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',  # 日志格式
    datefmt='%Y-%m-%d %H:%M:%S'  # 时间格式
)

# 创建logger对象
# logger是logging模块的核心对象，用于记录日志
logger = logging.getLogger(__name__)  # __name__表示当前模块名

# 使用不同级别记录日志
print("\n记录不同级别的日志消息：")
logger.debug("这是一条DEBUG级别的日志消息 - 用于调试")
logger.info("这是一条INFO级别的日志消息 - 程序正常运行")
logger.warning("这是一条WARNING级别的日志消息 - 可能出现问题")
logger.error("这是一条ERROR级别的日志消息 - 发生错误")
logger.critical("这是一条CRITICAL级别的日志消息 - 严重错误")

# ============================================
# 第三部分：理解日志级别过滤
# ============================================

print("\n" + "=" * 50)
print("理解日志级别过滤")
print("=" * 50)

# 重新配置logger，只记录WARNING及以上级别的日志
print("\n配置只记录WARNING及以上级别的日志：")
logging.basicConfig(
    level=logging.WARNING,  # 只记录WARNING及以上级别的日志
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 重新获取logger
logger = logging.getLogger(__name__)

# 再次记录日志，只有WARNING及以上级别的会被记录
print("尝试记录不同级别的日志：")
logger.debug("DEBUG消息 - 不会被记录")
logger.info("INFO消息 - 不会被记录")
logger.warning("WARNING消息 - 会被记录")
logger.error("ERROR消息 - 会被记录")

# ============================================
# 第四部分：日志输出到文件
# ============================================

print("\n" + "=" * 50)
print("日志输出到文件")
print("=" * 50)

# 配置日志同时输出到控制台和文件
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('app.log'),  # 输出到文件
        logging.StreamHandler()  # 输出到控制台
    ]
)

logger = logging.getLogger(__name__)

# 记录一些日志到文件
logger.info("这条日志会同时输出到控制台和app.log文件")
logger.error("错误信息也会被记录到文件")

print("\n日志已保存到app.log文件中")

# ============================================
# 第五部分：自定义日志格式
# ============================================

print("\n" + "=" * 50)
print("自定义日志格式")
print("=" * 50)

# 创建自定义的Formatter对象
formatter = logging.Formatter(
    fmt='[%(levelname)s] %(asctime)s [%(filename)s:%(lineno)d] - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

# 创建handler并设置格式
console_handler = logging.StreamHandler()
console_handler.setFormatter(formatter)

# 创建logger并添加handler
logger = logging.getLogger('custom_logger')
logger.setLevel(logging.DEBUG)
logger.addHandler(console_handler)

# 使用自定义格式记录日志
logger.debug("自定义格式的DEBUG日志")
logger.info("自定义格式的INFO日志")
logger.warning("自定义格式的WARNING日志")

# ============================================
# 第六部分：日志实战练习
# ============================================

print("\n" + "=" * 50)
print("日志实战练习")
print("=" * 50)

def calculate_average(numbers):
    """
    计算列表的平均值，并记录日志
    """
    logger = logging.getLogger('calculator')

    logger.info(f"开始计算平均值，输入数据: {numbers}")

    if not numbers:
        logger.error("输入列表为空，无法计算平均值")
        return None

    try:
        total = sum(numbers)
        count = len(numbers)
        average = total / count

        logger.debug(f"计算过程: 总和={total}, 数量={count}")
        logger.info(f"计算完成，平均值: {average}")

        return average
    except Exception as e:
        logger.error(f"计算平均值时发生错误: {e}")
        return None

# 配置练习用的logger
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 测试函数
print("测试calculate_average函数:")
result1 = calculate_average([1, 2, 3, 4, 5])
print(f"结果1: {result1}")

result2 = calculate_average([])
print(f"结果2: {result2}")

# ============================================
# 第七部分：知识点总结
# ============================================

print("\n" + "=" * 50)
print("知识点总结")
print("=" * 50)

summary = """
必须背下来的知识点：
1. 6个日志级别：DEBUG < INFO < WARNING < ERROR < CRITICAL
2. logging.basicConfig() - 基本日志配置方法
3. logging.getLogger(name) - 获取logger对象
4. logger.debug()/info()/warning()/error()/critical() - 记录日志的方法

需要熟悉掌握的知识点：
1. 日志格式字符串中的占位符：%(asctime)s, %(name)s, %(levelname)s, %(message)s
2. 日志输出目标：控制台(StreamHandler) vs 文件(FileHandler)
3. 日志级别过滤：通过level参数控制记录哪些级别的日志

了解即可的知识点：
1. Formatter类 - 用于自定义日志格式
2. Handler类 - 用于控制日志输出目标
3. Filter类 - 用于过滤特定日志（高级用法）
"""

print(summary)

print("\n" + "=" * 50)
print("基础层学习完成！")
print("下一步：学习日志与Web框架的集成")
print("=" * 50)