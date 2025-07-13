import aiosqlite
from loguru import logger
from typing import Optional
from contextlib import asynccontextmanager

class AsyncDbManager:
    def __init__(self):
        self._connections = {}  # 存储数据库连接

    @asynccontextmanager
    async def get_connection(self, db_path: str):
        """
        异步获取数据库连接
        使用方法:
        async with db_manager.get_connection(db_path) as conn:
            async with conn.execute(...) as cursor:
                ...
        """
        try:
            if db_path not in self._connections:
                self._connections[db_path] = await aiosqlite.connect(db_path)
            conn = self._connections[db_path]
            yield conn
        except Exception as e:
            logger.error(f"数据库连接错误: {e}")
            raise
            
    async def close_all(self):
        """关闭所有数据库连接"""
        for conn in self._connections.values():
            await conn.close()
        self._connections.clear()

# 全局数据库管理器实例
db_manager = AsyncDbManager()

async def create_table(db_path: str, table_name: str, columns: str) -> bool:
    """
    异步创建数据表
    :param db_path: 数据库路径
    :param table_name: 表名
    :param columns: 列定义
    :return: 是否成功
    """
    try:
        async with db_manager.get_connection(db_path) as conn:
            await conn.execute(
                f"CREATE TABLE IF NOT EXISTS `{table_name}` ({columns})"
            )
            await conn.commit()
            return True
    except Exception as e:
        logger.error(f'创建数据表出现错误, 错误信息: {e}')
        return False