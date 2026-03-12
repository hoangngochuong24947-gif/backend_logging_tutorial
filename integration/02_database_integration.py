"""
后端日志教学 - 联合层：日志与数据库集成
文件名：02_database_integration.py
功能：学习如何在数据库操作中使用日志系统

教学目标：
1. 掌握数据库连接池的日志记录
2. 学习SQL查询的日志记录
3. 了解数据库事务的日志跟踪
4. 掌握数据库错误处理和恢复日志
"""

import logging
import logging.config
import time
from datetime import datetime
from contextlib import contextmanager
from typing import Optional, Dict, Any, List
import sqlite3
import json

print("=" * 80)
print("数据库日志集成")
print("=" * 80)

# ============================================
# 第一部分：数据库日志配置
# ============================================

print("\n" + "=" * 50)
print("第一部分：数据库日志配置")
print("=" * 50)

# 数据库操作的日志配置
DATABASE_LOGGING_CONFIG = {
    'version': 1,
    'disable_existing_loggers': False,

    'formatters': {
        'standard': {
            'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'sql': {
            'format': '%(asctime)s [SQL] %(message)s',
            'datefmt': '%H:%M:%S'
        },
        'transaction': {
            'format': '%(asctime)s [TX] %(message)s',
            'datefmt': '%H:%M:%S.%f'
        }
    },

    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'db_file': {
            'class': 'logging.FileHandler',
            'filename': 'database_operations.log',
            'level': 'DEBUG',
            'formatter': 'standard',
            'encoding': 'utf-8'
        },
        'sql_file': {
            'class': 'logging.FileHandler',
            'filename': 'sql_queries.log',
            'level': 'DEBUG',
            'formatter': 'sql',
            'encoding': 'utf-8'
        },
        'transaction_file': {
            'class': 'logging.FileHandler',
            'filename': 'transactions.log',
            'level': 'INFO',
            'formatter': 'transaction',
            'encoding': 'utf-8'
        },
        'error_file': {
            'class': 'logging.FileHandler',
            'filename': 'database_errors.log',
            'level': 'ERROR',
            'formatter': 'standard',
            'encoding': 'utf-8'
        }
    },

    'loggers': {
        'database': {  # 数据库主logger
            'handlers': ['console', 'db_file'],
            'level': 'INFO',
            'propagate': False
        },
        'database.connection': {  # 连接池相关日志
            'handlers': ['db_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'database.sql': {  # SQL查询日志
            'handlers': ['sql_file'],
            'level': 'DEBUG',
            'propagate': False
        },
        'database.transaction': {  # 事务日志
            'handlers': ['transaction_file'],
            'level': 'INFO',
            'propagate': False
        },
        'database.error': {  # 数据库错误日志
            'handlers': ['error_file'],
            'level': 'ERROR',
            'propagate': False
        }
    }
}

# 应用配置
logging.config.dictConfig(DATABASE_LOGGING_CONFIG)

print("数据库日志配置已加载")
print("- 数据库操作日志: database_operations.log")
print("- SQL查询日志: sql_queries.log")
print("- 事务日志: transactions.log")
print("- 数据库错误日志: database_errors.log")

# 获取logger
db_logger = logging.getLogger('database')
connection_logger = logging.getLogger('database.connection')
sql_logger = logging.getLogger('database.sql')
transaction_logger = logging.getLogger('database.transaction')
error_logger = logging.getLogger('database.error')

# ============================================
# 第二部分：带日志的数据库连接池
# ============================================

print("\n" + "=" * 50)
print("第二部分：带日志的数据库连接池")
print("=" * 50)

class DatabaseConnectionPool:
    """带日志的数据库连接池"""

    def __init__(self, db_path: str, pool_size: int = 5):
        self.db_path = db_path
        self.pool_size = pool_size
        self.pool: List[sqlite3.Connection] = []
        self.in_use: Dict[int, bool] = {}
        self.connection_count = 0

        db_logger.info(f"初始化数据库连接池: {db_path}, 大小: {pool_size}")
        connection_logger.debug(f"连接池参数: path={db_path}, pool_size={pool_size}")

        # 初始化连接池
        self._initialize_pool()

    def _initialize_pool(self):
        """初始化连接池"""
        connection_logger.info("开始初始化连接池")

        for i in range(self.pool_size):
            try:
                conn = sqlite3.connect(self.db_path, check_same_thread=False)
                conn.row_factory = sqlite3.Row  # 使用行工厂
                self.pool.append(conn)
                self.in_use[id(conn)] = False
                self.connection_count += 1

                connection_logger.debug(f"创建连接 {i+1}/{self.pool_size}: id={id(conn)}")
            except Exception as e:
                error_logger.error(f"创建数据库连接失败: {e}", exc_info=True)
                raise

        connection_logger.info(f"连接池初始化完成，共 {len(self.pool)} 个连接")

    def get_connection(self) -> sqlite3.Connection:
        """从连接池获取连接"""
        connection_logger.debug("尝试获取数据库连接")

        for conn in self.pool:
            conn_id = id(conn)
            if not self.in_use[conn_id]:
                self.in_use[conn_id] = True
                connection_logger.info(f"获取连接: id={conn_id}")
                connection_logger.debug(f"可用连接: {self._available_connections()}/{self.pool_size}")
                return conn

        # 没有可用连接
        error_logger.warning("连接池耗尽，无可用连接")
        raise ConnectionError("数据库连接池耗尽")

    def release_connection(self, conn: sqlite3.Connection):
        """释放连接回连接池"""
        conn_id = id(conn)
        if conn_id in self.in_use:
            self.in_use[conn_id] = False
            connection_logger.info(f"释放连接: id={conn_id}")
            connection_logger.debug(f"可用连接: {self._available_connections()}/{self.pool_size}")
        else:
            error_logger.error(f"尝试释放未知连接: id={conn_id}")

    def _available_connections(self) -> int:
        """获取可用连接数量"""
        return sum(1 for in_use in self.in_use.values() if not in_use)

    def close_all(self):
        """关闭所有连接"""
        connection_logger.info("开始关闭所有数据库连接")

        for conn in self.pool:
            try:
                conn.close()
                connection_logger.debug(f"关闭连接: id={id(conn)}")
            except Exception as e:
                error_logger.error(f"关闭连接时出错: {e}")

        self.pool.clear()
        self.in_use.clear()

        db_logger.info("所有数据库连接已关闭")

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close_all()

# ============================================
# 第三部分：带日志的数据库操作封装
# ============================================

print("\n" + "=" * 50)
print("第三部分：带日志的数据库操作封装")
print("=" * 50)

class DatabaseManager:
    """数据库管理器，封装所有数据库操作"""

    def __init__(self, connection_pool: DatabaseConnectionPool):
        self.pool = connection_pool
        db_logger.info(f"初始化DatabaseManager，连接池大小: {connection_pool.pool_size}")

    @contextmanager
    def get_cursor(self):
        """
        获取数据库游标的上下文管理器
        自动管理连接的获取和释放
        """
        conn = None
        cursor = None

        try:
            # 获取连接
            conn = self.pool.get_connection()
            cursor = conn.cursor()

            connection_logger.debug(f"获取游标，连接id={id(conn)}")

            yield cursor

            # 提交事务
            conn.commit()
            connection_logger.debug(f"提交事务，连接id={id(conn)}")

        except Exception as e:
            # 回滚事务
            if conn:
                conn.rollback()
                connection_logger.warning(f"回滚事务，连接id={id(conn)}，错误: {e}")

            error_logger.error(f"数据库操作失败: {e}", exc_info=True)
            raise

        finally:
            # 释放连接
            if cursor:
                cursor.close()
                connection_logger.debug(f"关闭游标，连接id={id(conn) if conn else 'unknown'}")

            if conn:
                self.pool.release_connection(conn)

    def execute_query(self, sql: str, params: tuple = None, query_name: str = None):
        """
        执行查询并记录日志

        Args:
            sql: SQL语句
            params: 参数
            query_name: 查询名称（用于日志）

        Returns:
            查询结果
        """
        query_id = f"{query_name or 'unnamed'}_{int(time.time() * 1000)}"

        # 记录SQL查询
        sql_logger.info(f"[{query_id}] 执行查询")
        sql_logger.debug(f"[{query_id}] SQL: {sql}")
        if params:
            sql_logger.debug(f"[{query_id}] 参数: {params}")

        start_time = time.time()

        try:
            with self.get_cursor() as cursor:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)

                result = cursor.fetchall()

                # 计算执行时间
                exec_time = time.time() - start_time

                # 记录查询结果
                sql_logger.info(f"[{query_id}] 查询成功，行数: {len(result)}，时间: {exec_time:.3f}s")
                sql_logger.debug(f"[{query_id}] 执行时间: {exec_time:.3f}s")

                if len(result) <= 5:  # 只记录少量结果
                    sql_logger.debug(f"[{query_id}] 结果: {result}")

                return result

        except Exception as e:
            exec_time = time.time() - start_time
            error_logger.error(
                f"[{query_id}] 查询失败，时间: {exec_time:.3f}s，错误: {e}",
                exc_info=True
            )
            raise

    def execute_update(self, sql: str, params: tuple = None, operation_name: str = None):
        """
        执行更新操作并记录日志

        Args:
            sql: SQL语句
            params: 参数
            operation_name: 操作名称（用于日志）

        Returns:
            影响的行数
        """
        operation_id = f"{operation_name or 'unnamed'}_{int(time.time() * 1000)}"

        # 记录更新操作
        sql_logger.info(f"[{operation_id}] 执行更新")
        sql_logger.debug(f"[{operation_id}] SQL: {sql}")
        if params:
            sql_logger.debug(f"[{operation_id}] 参数: {params}")

        start_time = time.time()

        try:
            with self.get_cursor() as cursor:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)

                affected_rows = cursor.rowcount

                # 计算执行时间
                exec_time = time.time() - start_time

                # 记录操作结果
                sql_logger.info(
                    f"[{operation_id}] 更新成功，"
                    f"影响行数: {affected_rows}，"
                    f"时间: {exec_time:.3f}s"
                )

                return affected_rows

        except Exception as e:
            exec_time = time.time() - start_time
            error_logger.error(
                f"[{operation_id}] 更新失败，时间: {exec_time:.3f}s，错误: {e}",
                exc_info=True
            )
            raise

# ============================================
# 第四部分：事务日志跟踪
# ============================================

print("\n" + "=" * 50)
print("第四部分：事务日志跟踪")
print("=" * 50)

class TransactionManager:
    """事务管理器，跟踪事务的完整生命周期"""

    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.transaction_id = None
        self.operations = []
        transaction_logger.info("初始化TransactionManager")

    @contextmanager
    def transaction(self, transaction_name: str = None):
        """
        事务上下文管理器

        Args:
            transaction_name: 事务名称
        """
        # 生成事务ID
        self.transaction_id = f"tx_{int(time.time() * 1000)}_{hash(transaction_name or '') & 0xffff}"
        self.operations = []

        transaction_logger.info(f"[{self.transaction_id}] 开始事务: {transaction_name or '未命名'}")
        transaction_logger.debug(f"[{self.transaction_id}] 事务详情: name={transaction_name}")

        start_time = time.time()

        try:
            yield self
            # 提交事务
            transaction_logger.info(f"[{self.transaction_id}] 准备提交事务")
            transaction_logger.debug(f"[{self.transaction_id}] 操作记录: {self.operations}")

            # 在实际应用中，这里会执行提交操作
            # 对于演示，我们只是记录日志

            exec_time = time.time() - start_time
            transaction_logger.info(
                f"[{self.transaction_id}] 事务提交成功，"
                f"操作数: {len(self.operations)}，"
                f"时间: {exec_time:.3f}s"
            )

        except Exception as e:
            # 回滚事务
            exec_time = time.time() - start_time
            transaction_logger.error(
                f"[{self.transaction_id}] 事务回滚，"
                f"操作数: {len(self.operations)}，"
                f"时间: {exec_time:.3f}s，"
                f"错误: {e}",
                exc_info=True
            )

            error_logger.error(
                f"[{self.transaction_id}] 事务失败，已回滚",
                exc_info=True
            )

            raise

        finally:
            # 清理
            self.transaction_id = None
            self.operations = []

    def record_operation(self, operation_type: str, details: Dict[str, Any]):
        """记录事务中的操作"""
        if self.transaction_id:
            operation = {
                'type': operation_type,
                'timestamp': datetime.now().isoformat(),
                'details': details
            }
            self.operations.append(operation)

            transaction_logger.debug(
                f"[{self.transaction_id}] 记录操作: {operation_type}",
                extra={'operation': operation}
            )

    def execute_in_transaction(self, sql: str, params: tuple = None, operation_name: str = None):
        """
        在事务中执行SQL操作

        Args:
            sql: SQL语句
            params: 参数
            operation_name: 操作名称

        Returns:
            操作结果
        """
        if not self.transaction_id:
            error_logger.error("尝试在事务外执行事务操作")
            raise RuntimeError("必须在事务上下文中执行")

        # 记录操作
        operation_type = 'UPDATE' if sql.strip().upper().startswith(('INSERT', 'UPDATE', 'DELETE')) else 'QUERY'
        self.record_operation(operation_type, {
            'sql': sql,
            'params': params,
            'name': operation_name
        })

        # 执行操作
        if operation_type == 'QUERY':
            return self.db_manager.execute_query(sql, params, operation_name)
        else:
            return self.db_manager.execute_update(sql, params, operation_name)

# ============================================
# 第五部分：数据模型与日志集成
# ============================================

print("\n" + "=" * 50)
print("第五部分：数据模型与日志集成")
print("=" * 50)

class UserModel:
    """用户模型，演示数据层与日志的集成"""

    def __init__(self, db_manager: DatabaseManager):
        self.db = db_manager
        db_logger.info("初始化UserModel")

    def create_table(self):
        """创建用户表"""
        sql = """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """

        try:
            self.db.execute_update(sql, operation_name="create_users_table")
            db_logger.info("用户表创建成功")
        except Exception as e:
            error_logger.error("创建用户表失败", exc_info=True)
            raise

    def create_user(self, username: str, email: str) -> int:
        """
        创建用户

        Args:
            username: 用户名
            email: 邮箱

        Returns:
            用户ID
        """
        db_logger.info(f"创建用户: username={username}, email={email}")

        sql = "INSERT INTO users (username, email) VALUES (?, ?)"
        params = (username, email)

        try:
            # 这里不直接调用execute_update，而是使用事务
            # 在实际应用中，可能需要更复杂的逻辑
            self.db.execute_update(sql, params, operation_name="create_user")
            db_logger.info(f"用户创建成功: {username}")

            # 获取最后插入的ID
            result = self.db.execute_query(
                "SELECT last_insert_rowid() as id",
                operation_name="get_last_user_id"
            )
            user_id = result[0]['id']

            db_logger.debug(f"新用户ID: {user_id}")
            return user_id

        except sqlite3.IntegrityError as e:
            if "UNIQUE constraint failed" in str(e):
                error_type = "用户名" if "username" in str(e) else "邮箱"
                error_logger.warning(f"{error_type}已存在: {username if 'username' in str(e) else email}")
                raise ValueError(f"{error_type}已存在")
            else:
                error_logger.error("创建用户时发生完整性错误", exc_info=True)
                raise
        except Exception as e:
            error_logger.error("创建用户失败", exc_info=True)
            raise

    def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """
        获取用户信息

        Args:
            user_id: 用户ID

        Returns:
            用户信息字典或None
        """
        db_logger.info(f"获取用户: id={user_id}")

        sql = "SELECT * FROM users WHERE id = ?"
        params = (user_id,)

        try:
            result = self.db.execute_query(sql, params, operation_name="get_user_by_id")

            if result:
                user = dict(result[0])
                db_logger.debug(f"找到用户: {user}")
                return user
            else:
                db_logger.warning(f"用户不存在: id={user_id}")
                return None

        except Exception as e:
            error_logger.error(f"获取用户失败: id={user_id}", exc_info=True)
            raise

    def update_user(self, user_id: int, **kwargs) -> bool:
        """
        更新用户信息

        Args:
            user_id: 用户ID
            **kwargs: 要更新的字段

        Returns:
            是否成功
        """
        db_logger.info(f"更新用户: id={user_id}, 更新字段: {kwargs}")

        if not kwargs:
            db_logger.warning("更新用户时未提供任何字段")
            return False

        # 构建SET子句
        set_clause = ", ".join([f"{k} = ?" for k in kwargs.keys()])
        sql = f"UPDATE users SET {set_clause}, updated_at = CURRENT_TIMESTAMP WHERE id = ?"

        # 参数：更新值 + 用户ID
        params = tuple(kwargs.values()) + (user_id,)

        try:
            affected_rows = self.db.execute_update(sql, params, operation_name="update_user")

            if affected_rows > 0:
                db_logger.info(f"用户更新成功: id={user_id}, 影响行数: {affected_rows}")
                return True
            else:
                db_logger.warning(f"用户不存在，无法更新: id={user_id}")
                return False

        except Exception as e:
            error_logger.error(f"更新用户失败: id={user_id}", exc_info=True)
            raise

    def delete_user(self, user_id: int) -> bool:
        """
        删除用户

        Args:
            user_id: 用户ID

        Returns:
            是否成功
        """
        db_logger.info(f"删除用户: id={user_id}")

        sql = "DELETE FROM users WHERE id = ?"
        params = (user_id,)

        try:
            affected_rows = self.db.execute_update(sql, params, operation_name="delete_user")

            if affected_rows > 0:
                db_logger.info(f"用户删除成功: id={user_id}")
                return True
            else:
                db_logger.warning(f"用户不存在，无法删除: id={user_id}")
                return False

        except Exception as e:
            error_logger.error(f"删除用户失败: id={user_id}", exc_info=True)
            raise

    def list_users(self, limit: int = 100, offset: int = 0) -> List[Dict[str, Any]]:
        """
        列出用户

        Args:
            limit: 限制数量
            offset: 偏移量

        Returns:
            用户列表
        """
        db_logger.info(f"列出用户: limit={limit}, offset={offset}")

        sql = "SELECT * FROM users ORDER BY id LIMIT ? OFFSET ?"
        params = (limit, offset)

        try:
            result = self.db.execute_query(sql, params, operation_name="list_users")

            db_logger.info(f"找到 {len(result)} 个用户")
            db_logger.debug(f"用户列表: {[dict(row) for row in result]}")

            return [dict(row) for row in result]

        except Exception as e:
            error_logger.error("列出用户失败", exc_info=True)
            raise

# ============================================
# 第六部分：完整示例演示
# ============================================

print("\n" + "=" * 50)
print("第六部分：完整示例演示")
print("=" * 50)

def demonstrate_database_logging():
    """演示数据库日志的完整流程"""

    print("\n开始演示数据库日志...")

    # 创建连接池
    with DatabaseConnectionPool(":memory:", pool_size=3) as pool:
        db_logger.info("=" * 50)
        db_logger.info("开始数据库日志演示")
        db_logger.info("=" * 50)

        # 创建数据库管理器
        db_manager = DatabaseManager(pool)

        # 创建用户模型
        user_model = UserModel(db_manager)

        # 1. 创建表
        print("\n1. 创建用户表...")
        user_model.create_table()

        # 2. 创建用户
        print("\n2. 创建用户...")
        try:
            user1_id = user_model.create_user("alice", "alice@example.com")
            print(f"  创建用户 alice, ID: {user1_id}")

            user2_id = user_model.create_user("bob", "bob@example.com")
            print(f"  创建用户 bob, ID: {user2_id}")

            # 测试重复用户
            try:
                user_model.create_user("alice", "alice2@example.com")
            except ValueError as e:
                print(f"  预期错误: {e}")

        except Exception as e:
            print(f"  创建用户失败: {e}")

        # 3. 查询用户
        print("\n3. 查询用户...")
        try:
            user = user_model.get_user(user1_id)
            print(f"  查询用户 {user1_id}: {user['username'] if user else '不存在'}")

            non_existent = user_model.get_user(999)
            print(f"  查询不存在的用户: {'不存在' if non_existent is None else '存在'}")

        except Exception as e:
            print(f"  查询用户失败: {e}")

        # 4. 更新用户
        print("\n4. 更新用户...")
        try:
            success = user_model.update_user(user1_id, email="alice.new@example.com")
            print(f"  更新用户 {user1_id}: {'成功' if success else '失败'}")

            user = user_model.get_user(user1_id)
            print(f"  更新后的邮箱: {user['email'] if user else 'N/A'}")

        except Exception as e:
            print(f"  更新用户失败: {e}")

        # 5. 列出用户
        print("\n5. 列出用户...")
        try:
            users = user_model.list_users(limit=10)
            print(f"  找到 {len(users)} 个用户")
            for u in users:
                print(f"    - {u['id']}: {u['username']} ({u['email']})")

        except Exception as e:
            print(f"  列出用户失败: {e}")

        # 6. 演示事务
        print("\n6. 演示事务...")
        try:
            transaction_mgr = TransactionManager(db_manager)

            with transaction_mgr.transaction("批量用户操作"):
                print("  开始事务操作...")

                # 在事务中执行多个操作
                transaction_mgr.execute_in_transaction(
                    "INSERT INTO users (username, email) VALUES (?, ?)",
                    ("charlie", "charlie@example.com"),
                    "insert_charlie"
                )

                transaction_mgr.execute_in_transaction(
                    "UPDATE users SET email = ? WHERE username = ?",
                    ("bob.new@example.com", "bob"),
                    "update_bob_email"
                )

                print("  事务操作完成")

        except Exception as e:
            print(f"  事务失败: {e}")

        # 7. 删除用户
        print("\n7. 删除用户...")
        try:
            success = user_model.delete_user(user2_id)
            print(f"  删除用户 {user2_id}: {'成功' if success else '失败'}")

            # 验证删除
            user = user_model.get_user(user2_id)
            print(f"  验证删除: {'不存在（正确）' if user is None else '存在（错误）'}")

        except Exception as e:
            print(f"  删除用户失败: {e}")

        # 8. 错误处理演示
        print("\n8. 错误处理演示...")
        try:
            # 执行无效SQL
            db_manager.execute_query("SELECT * FROM non_existent_table")
        except Exception as e:
            print(f"  预期错误: {type(e).__name__}")

        db_logger.info("=" * 50)
        db_logger.info("数据库日志演示完成")
        db_logger.info("=" * 50)

    print("\n演示完成！")
    print("\n生成的日志文件:")
    print("- database_operations.log: 数据库操作日志")
    print("- sql_queries.log: SQL查询日志")
    print("- transactions.log: 事务日志")
    print("- database_errors.log: 数据库错误日志")

# 运行演示
demonstrate_database_logging()

# ============================================
# 第七部分：知识点总结
# ============================================

print("\n" + "=" * 50)
print("知识点总结")
print("=" * 50)

summary = """
必须背下来的知识点：
1. 数据库连接池的日志记录 - 记录连接的获取、释放和状态
2. SQL查询日志 - 记录SQL语句、参数、执行时间和结果
3. 事务日志跟踪 - 记录事务的开始、提交、回滚和操作历史
4. 数据库错误分类记录 - 区分完整性错误、连接错误、语法错误等

需要熟悉掌握的知识点：
1. 上下文管理器在数据库操作中的应用 - 自动管理连接和事务
2. 查询性能日志 - 记录查询执行时间和优化建议
3. 数据模型层的日志集成 - 在业务逻辑中记录相关操作
4. 连接池监控日志 - 监控连接使用情况和性能指标

了解即可的知识点：
1. 慢查询日志 - 记录执行时间超过阈值的查询
2. 数据库死锁检测和日志记录
3. 数据库备份和恢复的日志记录
4. 数据库迁移脚本的日志记录
"""

print(summary)

print("\n" + "=" * 50)
print("数据库集成学习完成！")
print("下一步：学习高级日志功能")
print("=" * 50)