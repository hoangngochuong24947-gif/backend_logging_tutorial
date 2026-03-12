"""
后端日志教学 - 联合层：日志性能优化
文件名：03_performance_optimization.py
功能：学习日志系统的性能优化技巧和最佳实践

教学目标：
1. 掌握日志性能评估方法
2. 学习异步日志处理
3. 了解日志采样和限流
4. 掌握结构化日志的性能优势
"""

import logging
import logging.config
import logging.handlers
import time
import statistics
import threading
import queue
import json
import gzip
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from typing import Dict, Any, List
import random

print("=" * 80)
print("日志性能优化")
print("=" * 80)

# ============================================
# 第一部分：日志性能基准测试
# ============================================

print("\n" + "=" * 50)
print("第一部分：日志性能基准测试")
print("=" * 50)

class LoggingBenchmark:
    """日志性能基准测试工具"""

    def __init__(self):
        self.results = {}
        self.setup_loggers()

    def setup_loggers(self):
        """设置测试用的logger"""

        # 1. 基础logger（无优化）
        basic_logger = logging.getLogger('benchmark.basic')
        basic_logger.setLevel(logging.DEBUG)

        # 添加文件handler
        basic_handler = logging.FileHandler('benchmark_basic.log', mode='w')
        basic_handler.setLevel(logging.DEBUG)
        basic_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        ))
        basic_logger.addHandler(basic_handler)
        basic_logger.propagate = False

        # 2. 异步logger
        async_logger = logging.getLogger('benchmark.async')
        async_logger.setLevel(logging.DEBUG)

        # 使用QueueHandler
        log_queue = queue.Queue(-1)
        queue_handler = logging.handlers.QueueHandler(log_queue)
        async_logger.addHandler(queue_handler)

        # 设置QueueListener
        async_handler = logging.FileHandler('benchmark_async.log', mode='w')
        async_handler.setLevel(logging.DEBUG)
        async_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        ))

        self.async_listener = logging.handlers.QueueListener(log_queue, async_handler)
        self.async_listener.start()

        async_logger.propagate = False

        # 3. 批量logger
        batch_logger = logging.getLogger('benchmark.batch')
        batch_logger.setLevel(logging.DEBUG)

        # 自定义handler，支持批量写入
        class BatchFileHandler(logging.FileHandler):
            def __init__(self, filename, batch_size=100):
                super().__init__(filename, mode='w')
                self.batch_size = batch_size
                self.batch_buffer = []

            def emit(self, record):
                self.batch_buffer.append(self.format(record))
                if len(self.batch_buffer) >= self.batch_size:
                    self.flush_batch()

            def flush_batch(self):
                if self.batch_buffer:
                    with open(self.filename, 'a', encoding='utf-8') as f:
                        f.write('\n'.join(self.batch_buffer) + '\n')
                    self.batch_buffer.clear()

            def close(self):
                self.flush_batch()
                super().close()

        batch_handler = BatchFileHandler('benchmark_batch.log', batch_size=50)
        batch_handler.setLevel(logging.DEBUG)
        batch_handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
        ))
        batch_logger.addHandler(batch_handler)
        batch_logger.propagate = False

        # 4. 结构化logger（JSON格式）
        json_logger = logging.getLogger('benchmark.json')
        json_logger.setLevel(logging.DEBUG)

        class JSONFormatter(logging.Formatter):
            def format(self, record):
                log_record = {
                    'timestamp': datetime.now().isoformat(),
                    'level': record.levelname,
                    'logger': record.name,
                    'message': record.getMessage(),
                    'module': record.module,
                    'function': record.funcName,
                    'line': record.lineno
                }
                if hasattr(record, 'extra'):
                    log_record.update(record.extra)
                return json.dumps(log_record)

        json_handler = logging.FileHandler('benchmark_json.log', mode='w')
        json_handler.setLevel(logging.DEBUG)
        json_handler.setFormatter(JSONFormatter())
        json_logger.addHandler(json_handler)
        json_logger.propagate = False

        self.loggers = {
            'basic': basic_logger,
            'async': async_logger,
            'batch': batch_logger,
            'json': json_logger
        }

    def run_benchmark(self, num_logs=1000, message_length=100):
        """
        运行性能基准测试

        Args:
            num_logs: 日志数量
            message_length: 消息长度
        """
        print(f"\n运行基准测试: {num_logs}条日志，消息长度{message_length}字符")

        # 生成测试消息
        test_messages = [
            f"测试日志消息 {i}: {'x' * (message_length - 20)}"
            for i in range(num_logs)
        ]

        results = {}

        for logger_name, logger in self.loggers.items():
            print(f"\n测试 {logger_name} logger...")

            # 预热
            for _ in range(10):
                logger.info("预热消息")

            # 运行测试
            start_time = time.time()
            execution_times = []

            for i, message in enumerate(test_messages):
                log_start = time.time()

                # 添加一些额外数据
                extra_data = {
                    'log_id': i,
                    'timestamp': time.time(),
                    'random_value': random.random()
                }

                if logger_name == 'json':
                    logger.info(message, extra={'extra': extra_data})
                else:
                    logger.info(message)

                log_end = time.time()
                execution_times.append((log_end - log_start) * 1000)  # 转换为毫秒

            end_time = time.time()
            total_time = end_time - start_time

            # 收集结果
            results[logger_name] = {
                'total_time': total_time,
                'logs_per_second': num_logs / total_time,
                'avg_latency_ms': statistics.mean(execution_times),
                'p95_latency_ms': statistics.quantiles(execution_times, n=20)[18],  # 95th percentile
                'p99_latency_ms': statistics.quantiles(execution_times, n=100)[98],  # 99th percentile
                'max_latency_ms': max(execution_times),
                'min_latency_ms': min(execution_times),
                'file_size': self.get_file_size(f'benchmark_{logger_name}.log')
            }

            print(f"  完成时间: {total_time:.3f}秒")
            print(f"  吞吐量: {results[logger_name]['logs_per_second']:.1f} 条/秒")
            print(f"  平均延迟: {results[logger_name]['avg_latency_ms']:.3f} 毫秒")

        self.results = results
        return results

    def get_file_size(self, filename):
        """获取文件大小"""
        try:
            import os
            return os.path.getsize(filename)
        except:
            return 0

    def print_comparison(self):
        """打印比较结果"""
        print("\n" + "=" * 60)
        print("性能比较结果")
        print("=" * 60)

        # 打印表格头
        print(f"{'Logger类型':<15} {'总时间(s)':<12} {'吞吐量(条/s)':<15} "
              f"{'平均延迟(ms)':<15} {'P95延迟(ms)':<15} {'文件大小(KB)':<12}")

        print("-" * 90)

        for logger_name, result in self.results.items():
            total_time = result['total_time']
            throughput = result['logs_per_second']
            avg_latency = result['avg_latency_ms']
            p95_latency = result['p95_latency_ms']
            file_size_kb = result['file_size'] / 1024

            print(f"{logger_name:<15} {total_time:<12.3f} {throughput:<15.1f} "
                  f"{avg_latency:<15.3f} {p95_latency:<15.3f} {file_size_kb:<12.1f}")

        print("\n关键发现:")
        fastest = min(self.results.items(), key=lambda x: x[1]['total_time'])
        slowest = max(self.results.items(), key=lambda x: x[1]['total_time'])
        print(f"  最快: {fastest[0]} ({fastest[1]['total_time']:.3f}秒)")
        print(f"  最慢: {slowest[0]} ({slowest[1]['total_time']:.3f}秒)")

        # 计算提升百分比
        if 'basic' in self.results and 'async' in self.results:
            basic_time = self.results['basic']['total_time']
            async_time = self.results['async']['total_time']
            improvement = (basic_time - async_time) / basic_time * 100
            print(f"  异步 vs 基础: {improvement:.1f}% 性能提升")

    def cleanup(self):
        """清理资源"""
        if hasattr(self, 'async_listener'):
            self.async_listener.stop()

# 运行基准测试
print("开始日志性能基准测试...")
benchmark = LoggingBenchmark()
results = benchmark.run_benchmark(num_logs=500, message_length=200)
benchmark.print_comparison()

# ============================================
# 第二部分：异步日志处理深入
# ============================================

print("\n" + "=" * 50)
print("第二部分：异步日志处理深入")
print("=" * 50)

class AsyncLoggingSystem:
    """完整的异步日志系统"""

    def __init__(self, max_queue_size=10000, num_workers=2):
        self.max_queue_size = max_queue_size
        self.num_workers = num_workers
        self.log_queue = queue.Queue(maxsize=max_queue_size)
        self.workers = []
        self.running = False

        print(f"初始化异步日志系统: 队列大小={max_queue_size}, 工作线程={num_workers}")

    def start(self):
        """启动异步日志系统"""
        if self.running:
            return

        print("启动异步日志系统...")
        self.running = True

        # 创建工作线程
        for i in range(self.num_workers):
            worker = threading.Thread(
                target=self._log_worker,
                name=f"LogWorker-{i}",
                daemon=True
            )
            worker.start()
            self.workers.append(worker)

        print(f"启动 {self.num_workers} 个日志工作线程")

    def stop(self, timeout=5):
        """停止异步日志系统"""
        if not self.running:
            return

        print("停止异步日志系统...")
        self.running = False

        # 等待工作线程完成
        for worker in self.workers:
            worker.join(timeout=timeout)

        print("异步日志系统已停止")

    def _log_worker(self):
        """日志工作线程"""
        thread_name = threading.current_thread().name

        # 创建工作线程专用的文件handler
        log_file = f'async_log_{thread_name}.log'
        handler = logging.FileHandler(log_file, encoding='utf-8')
        handler.setFormatter(logging.Formatter(
            '%(asctime)s [%(levelname)s] [%(threadName)s] %(message)s'
        ))

        logs_processed = 0
        batch_size = 100
        batch_buffer = []

        print(f"{thread_name}: 开始处理日志，输出到 {log_file}")

        while self.running or not self.log_queue.empty():
            try:
                # 获取日志记录，设置超时
                log_record = self.log_queue.get(timeout=1)
                batch_buffer.append(log_record)
                logs_processed += 1

                # 批量处理
                if len(batch_buffer) >= batch_size:
                    self._process_batch(batch_buffer, handler)
                    batch_buffer.clear()

                self.log_queue.task_done()

            except queue.Empty:
                # 队列为空，处理剩余批次
                if batch_buffer:
                    self._process_batch(batch_buffer, handler)
                    batch_buffer.clear()
                continue

            except Exception as e:
                print(f"{thread_name}: 处理日志时出错: {e}")
                continue

        # 处理剩余日志
        if batch_buffer:
            self._process_batch(batch_buffer, handler)

        handler.close()
        print(f"{thread_name}: 处理完成，共处理 {logs_processed} 条日志")

    def _process_batch(self, batch, handler):
        """批量处理日志记录"""
        for record in batch:
            try:
                handler.emit(record)
            except Exception as e:
                print(f"写入日志失败: {e}")

    def log(self, level, message, **kwargs):
        """
        记录日志

        Args:
            level: 日志级别
            message: 日志消息
            **kwargs: 额外参数
        """
        if not self.running:
            raise RuntimeError("异步日志系统未启动")

        # 创建日志记录
        record = logging.LogRecord(
            name='async.system',
            level=level,
            pathname=__file__,
            lineno=0,
            msg=message,
            args=(),
            exc_info=None
        )

        # 添加额外字段
        for key, value in kwargs.items():
            setattr(record, key, value)

        # 添加到队列（非阻塞）
        try:
            self.log_queue.put_nowait(record)
            return True
        except queue.Full:
            # 队列满时的处理策略
            print("警告: 日志队列已满，丢弃日志")
            return False

    def get_stats(self):
        """获取统计信息"""
        return {
            'queue_size': self.log_queue.qsize(),
            'queue_max': self.max_queue_size,
            'queue_usage': self.log_queue.qsize() / self.max_queue_size * 100,
            'workers': len(self.workers),
            'running': self.running
        }

# 演示异步日志系统
print("\n演示异步日志系统...")

async_system = AsyncLoggingSystem(max_queue_size=5000, num_workers=3)

try:
    # 启动系统
    async_system.start()

    # 模拟高并发日志记录
    print("\n模拟高并发日志记录...")

    def log_producer(producer_id, num_logs):
        """日志生产者线程"""
        for i in range(num_logs):
            level = random.choice([logging.INFO, logging.DEBUG, logging.WARNING])
            message = f"生产者{producer_id}: 日志消息{i}"
            success = async_system.log(level, message, producer_id=producer_id, log_id=i)

            if not success and i % 100 == 0:
                print(f"生产者{producer_id}: 日志队列可能已满")

            # 随机延迟
            time.sleep(random.uniform(0.001, 0.01))

    # 创建多个生产者线程
    producers = []
    for i in range(5):
        producer = threading.Thread(
            target=log_producer,
            args=(i, 200),
            name=f"Producer-{i}",
            daemon=True
        )
        producer.start()
        producers.append(producer)

    # 监控队列状态
    print("\n监控队列状态 (5秒)...")
    for _ in range(5):
        stats = async_system.get_stats()
        print(f"  队列: {stats['queue_size']}/{stats['queue_max']} "
              f"({stats['queue_usage']:.1f}%)")
        time.sleep(1)

    # 等待生产者完成
    for producer in producers:
        producer.join(timeout=2)

    print("\n所有生产者完成")

    # 显示最终统计
    stats = async_system.get_stats()
    print(f"\n最终统计:")
    print(f"  队列大小: {stats['queue_size']}")
    print(f"  工作线程: {stats['workers']}")
    print(f"  运行状态: {stats['running']}")

finally:
    # 停止系统
    async_system.stop()

print("\n异步日志文件已生成:")
print("- async_log_LogWorker-0.log")
print("- async_log_LogWorker-1.log")
print("- async_log_LogWorker-2.log")

# ============================================
# 第三部分：日志采样和限流
# ============================================

print("\n" + "=" * 50)
print("第三部分：日志采样和限流")
print("=" * 50)

class SampledLogger:
    """支持采样和限流的日志器"""

    def __init__(self, base_logger, sample_rate=0.1, rate_limit=None):
        """
        初始化采样日志器

        Args:
            base_logger: 基础logger
            sample_rate: 采样率 (0.0-1.0)
            rate_limit: 速率限制 (条/秒)
        """
        self.base_logger = base_logger
        self.sample_rate = sample_rate
        self.rate_limit = rate_limit

        # 限流相关
        self.tokens = rate_limit if rate_limit else float('inf')
        self.last_update = time.time()
        self.token_refill_rate = rate_limit if rate_limit else float('inf')
        self.max_tokens = rate_limit if rate_limit else float('inf')

        print(f"初始化采样日志器: 采样率={sample_rate}, 限流={rate_limit}条/秒")

    def _check_rate_limit(self):
        """检查速率限制"""
        if self.rate_limit is None:
            return True

        now = time.time()
        elapsed = now - self.last_update

        # 补充令牌
        self.tokens = min(
            self.max_tokens,
            self.tokens + elapsed * self.token_refill_rate
        )
        self.last_update = now

        # 检查是否有可用令牌
        if self.tokens >= 1:
            self.tokens -= 1
            return True
        else:
            return False

    def _should_sample(self):
        """决定是否采样"""
        return random.random() <= self.sample_rate

    def log(self, level, message, force=False, **kwargs):
        """
        记录日志

        Args:
            level: 日志级别
            message: 日志消息
            force: 是否强制记录（忽略采样和限流）
            **kwargs: 额外参数
        """
        # 检查限流
        if not force and not self._check_rate_limit():
            return False

        # 检查采样
        if not force and not self._should_sample():
            return False

        # 记录日志
        if hasattr(self.base_logger, level.lower()):
            log_method = getattr(self.base_logger, level.lower())
            log_method(message, **kwargs)
        else:
            self.base_logger.log(level, message, **kwargs)

        return True

    def debug(self, message, force=False, **kwargs):
        return self.log(logging.DEBUG, message, force, **kwargs)

    def info(self, message, force=False, **kwargs):
        return self.log(logging.INFO, message, force, **kwargs)

    def warning(self, message, force=False, **kwargs):
        return self.log(logging.WARNING, message, force, **kwargs)

    def error(self, message, force=False, **kwargs):
        return self.log(logging.ERROR, message, force, **kwargs)

# 演示采样和限流
print("\n演示采样和限流...")

# 创建基础logger
sampled_logger = logging.getLogger('sampled')
sampled_handler = logging.FileHandler('sampled.log', mode='w')
sampled_handler.setFormatter(logging.Formatter(
    '%(asctime)s [%(levelname)s] %(message)s'
))
sampled_logger.addHandler(sampled_handler)
sampled_logger.setLevel(logging.DEBUG)

# 创建采样日志器
sampled = SampledLogger(
    base_logger=sampled_logger,
    sample_rate=0.3,  # 30%采样率
    rate_limit=100    # 100条/秒
)

print(f"配置: 采样率=30%，限流=100条/秒")
print("模拟记录500条DEBUG日志...")

recorded = 0
dropped = 0
start_time = time.time()

for i in range(500):
    success = sampled.debug(f"调试日志 {i}", extra={'log_id': i})

    if success:
        recorded += 1
    else:
        dropped += 1

    # 控制速率
    time.sleep(0.001)  # 1ms间隔，理论最大1000条/秒，但被限流到100条/秒

end_time = time.time()
actual_rate = recorded / (end_time - start_time)

print(f"\n结果:")
print(f"  记录: {recorded} 条")
print(f"  丢弃: {dropped} 条")
print(f"  记录率: {recorded/500*100:.1f}%")
print(f"  实际速率: {actual_rate:.1f} 条/秒")
print(f"  目标限流: 100 条/秒")

# ============================================
# 第四部分：结构化日志和压缩
# ============================================

print("\n" + "=" * 50)
print("第四部分：结构化日志和压缩")
print("=" * 50)

class CompressedStructuredLogger:
    """支持压缩的结构化日志器"""

    def __init__(self, log_file, compress=True, batch_size=100):
        self.log_file = log_file
        self.compress = compress
        self.batch_size = batch_size
        self.batch_buffer = []

        # 压缩文件扩展名
        if compress:
            self.actual_file = log_file + '.gz'
        else:
            self.actual_file = log_file

        print(f"初始化压缩日志器: 文件={self.actual_file}, "
              f"批量大小={batch_size}, 压缩={compress}")

    def _write_batch(self):
        """写入批次"""
        if not self.batch_buffer:
            return

        try:
            if self.compress:
                # 压缩写入
                with gzip.open(self.actual_file, 'at', encoding='utf-8') as f:
                    f.write('\n'.join(self.batch_buffer) + '\n')
            else:
                # 普通写入
                with open(self.actual_file, 'a', encoding='utf-8') as f:
                    f.write('\n'.join(self.batch_buffer) + '\n')

            self.batch_buffer.clear()

        except Exception as e:
            print(f"写入日志文件失败: {e}")

    def log(self, level: str, message: str, **kwargs):
        """
        记录结构化日志

        Args:
            level: 日志级别
            message: 日志消息
            **kwargs: 结构化字段
        """
        # 构建结构化日志记录
        log_record = {
            'timestamp': datetime.now().isoformat(),
            'level': level,
            'message': message,
            **kwargs
        }

        # 转换为JSON
        try:
            json_record = json.dumps(log_record, ensure_ascii=False)
            self.batch_buffer.append(json_record)

            # 检查是否达到批次大小
            if len(self.batch_buffer) >= self.batch_size:
                self._write_batch()

        except Exception as e:
            print(f"构建日志记录失败: {e}")

    def flush(self):
        """刷新缓冲区"""
        self._write_batch()

    def close(self):
        """关闭日志器"""
        self.flush()

    def get_file_size(self):
        """获取文件大小"""
        try:
            import os
            if os.path.exists(self.actual_file):
                return os.path.getsize(self.actual_file)
            return 0
        except:
            return 0

# 演示结构化日志和压缩
print("\n演示结构化日志和压缩...")

# 创建两个日志器进行对比
uncompressed_logger = CompressedStructuredLogger(
    'structured_uncompressed.log',
    compress=False,
    batch_size=50
)

compressed_logger = CompressedStructuredLogger(
    'structured_compressed.log',
    compress=True,
    batch_size=50
)

print("记录1000条结构化日志...")

# 记录日志
for i in range(1000):
    # 构建结构化数据
    user_data = {
        'user_id': f"user_{i % 100}",
        'action': random.choice(['login', 'view', 'purchase', 'logout']),
        'duration_ms': random.randint(10, 5000),
        'success': random.choice([True, False]),
        'ip_address': f"192.168.{random.randint(1, 255)}.{random.randint(1, 255)}"
    }

    # 选择日志级别
    if not user_data['success']:
        level = 'ERROR'
    elif user_data['duration_ms'] > 1000:
        level = 'WARNING'
    else:
        level = 'INFO'

    # 记录到两个日志器
    uncompressed_logger.log(level, f"用户操作: {user_data['action']}", **user_data)
    compressed_logger.log(level, f"用户操作: {user_data['action']}", **user_data)

# 刷新缓冲区
uncompressed_logger.flush()
compressed_logger.flush()

# 获取文件大小
uncompressed_size = uncompressed_logger.get_file_size()
compressed_size = compressed_logger.get_file_size()

print(f"\n文件大小对比:")
print(f"  未压缩: {uncompressed_size / 1024:.1f} KB")
print(f"  压缩后: {compressed_size / 1024:.1f} KB")
print(f"  压缩率: {(1 - compressed_size / uncompressed_size) * 100:.1f}%")

# 关闭日志器
uncompressed_logger.close()
compressed_logger.close()

print("\n结构化日志文件已生成:")
print(f"  - structured_uncompressed.log ({uncompressed_size} 字节)")
print(f"  - structured_compressed.log.gz ({compressed_size} 字节)")

# ============================================
# 第五部分：知识点总结
# ============================================

print("\n" + "=" * 50)
print("知识点总结")
print("=" * 50)

summary = """
必须背下来的知识点：
1. 性能基准测试方法 - 测量吞吐量、延迟、资源使用
2. 异步日志处理 - 使用QueueHandler和QueueListener减少I/O阻塞
3. 日志采样策略 - 控制DEBUG等低级别日志的数量
4. 速率限制实现 - 防止日志洪水影响系统性能

需要熟悉掌握的知识点：
1. 批量写入优化 - 减少文件系统调用次数
2. 结构化日志压缩 - 减少存储空间和I/O开销
3. 工作线程池配置 - 根据CPU核心数和工作负载调整线程数
4. 内存队列管理 - 防止内存溢出，设置合理的队列大小

了解即可的知识点：
1. 零拷贝日志技术 - 减少内存复制开销
2. 内存映射文件 - 提高大日志文件的写入性能
3. 日志分级存储 - 热数据、温数据、冷数据的不同存储策略
4. 实时性能监控 - 监控日志系统的健康状态和性能指标
"""

print(summary)

print("\n" + "=" * 50)
print("性能优化学习完成！")
print("下一步：学习高级日志功能")
print("=" * 50)

# 清理基准测试
benchmark.cleanup()