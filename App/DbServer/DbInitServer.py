from DbServer.DbDomServer import *
import Config.ConfigServer as Cs
from Config.logger import logger
from loguru import logger
from typing import Optional, List, Dict, Any
from .DbDomServer import db_manager

class DbInitServer:
    def __init__(self):
        """初始化数据库路径"""
        self.admin_db = Cs.returnAdminDbPath()
    async def init_admin_db(self) -> bool:
        """初始化管理员数据库"""
        try:
            async with db_manager.get_connection(self.admin_db) as conn:
                # 创建管理员表
                await conn.execute(
                    """CREATE TABLE IF NOT EXISTS admin
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    wxid TEXT NOT NULL UNIQUE,
                    group_id TEXT NOT NULL)"""
                )
                
                # 创建群组模式表
                await conn.execute(
                    """CREATE TABLE IF NOT EXISTS group_mode
                    (id INTEGER PRIMARY KEY AUTOINCREMENT,
                    group_id TEXT NOT NULL UNIQUE,
                    mode INTEGER NOT NULL DEFAULT 0)"""
                )
                
                # 创建插件配置表 - 保持与原结构一致
                await conn.execute(
                    """CREATE TABLE IF NOT EXISTS plugin_config
                    (mode TEXT NOT NULL,
                    plugin_name TEXT NOT NULL,
                    enabled INTEGER NOT NULL DEFAULT 1,
                    UNIQUE(mode, plugin_name))"""
                )
                
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f'初始化管理员数据库出错: {e}')
            return False
            
    async def init_all_databases(self) -> Dict[str, bool]:
        """初始化所有数据库"""
        results = {
            'admin_db': await self.init_admin_db(),
        }
        
        success = all(results.values())
        if success:
            logger.info('所有数据库初始化成功')
        else:
            failed_dbs = [db for db, result in results.items() if not result]
            logger.error(f'以下数据库初始化失败: {", ".join(failed_dbs)}')
            
        return results
            
    async def check_database(self, db_path: str) -> Dict[str, bool]:
        """检查指定数据库中的表是否存在"""
        try:
            async with db_manager.get_connection(db_path) as conn:
                async with conn.execute(
                    """SELECT name FROM sqlite_master 
                    WHERE type='table'"""
                ) as cursor:
                    tables = [row[0] for row in await cursor.fetchall()]
                    return {table: True for table in tables}
        except Exception as e:
            logger.error(f'检查数据库出错: {e}')
            return {}
            
    async def check_all_databases(self) -> Dict[str, Dict[str, bool]]:
        """检查所有数据库的状态"""
        return {
            'admin_db': await self.check_database(self.admin_db),
        }

if __name__ == '__main__':
    import asyncio
    
    async def main():
        db_init = DbInitServer()
        await db_init.init_all_databases()
        
    asyncio.run(main())
