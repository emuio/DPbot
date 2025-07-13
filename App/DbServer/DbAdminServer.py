from loguru import logger
from typing import Optional, List, Dict
from .DbDomServer import db_manager
import Config.ConfigServer as Cs

class DbAdminServer:
    def __init__(self):
        self.db_path = Cs.returnAdminDbPath()

    async def add_admin(self, group_id: str, wxid: str) -> bool:
        """添加管理员"""
        try:
            async with db_manager.get_connection(self.db_path) as conn:
                await conn.execute(
                    """INSERT INTO admin (group_id, wxid)
                    VALUES (?, ?)""",
                    (group_id, wxid)
                )
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f'添加管理员出错: {e}')
            return False

    async def delete_admin(self, group_id: str, wxid: str) -> bool:
        """删除管理员"""
        try:
            async with db_manager.get_connection(self.db_path) as conn:
                await conn.execute(
                    """DELETE FROM admin 
                    WHERE group_id=? AND wxid=?""",
                    (group_id, wxid)
                )
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f'删除管理员出错: {e}')
            return False

    async def query_admin(self, group_id: str, wxid: str) -> bool:
        """查询是否为管理员"""
        try:
            async with db_manager.get_connection(self.db_path) as conn:
                async with conn.execute(
                    """SELECT 1 FROM admin 
                    WHERE group_id=? AND wxid=?""",
                    (group_id, wxid)
                ) as cursor:
                    result = await cursor.fetchone()
                    return bool(result)
        except Exception as e:
            logger.error(f'查询管理员出错: {e}')
            return False

    async def set_group_mode(self, group_id: str, mode: int) -> bool:
        """设置群组模式"""
        try:
            async with db_manager.get_connection(self.db_path) as conn:
                await conn.execute(
                    """INSERT INTO group_mode (group_id, mode)
                    VALUES (?, ?)
                    ON CONFLICT(group_id) 
                    DO UPDATE SET mode = ?""",
                    (group_id, mode, mode)
                )
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f'设置群组模式出错: {e}')
            return False

    async def delete_group_mode(self, group_id: str) -> bool:
        """删除群组模式"""
        try:
            async with db_manager.get_connection(self.db_path) as conn:
                await conn.execute(
                    "DELETE FROM group_mode WHERE group_id=?",
                    (group_id,)
                )
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f'删除群组模式出错: {e}')
            return False

    async def query_group_mode(self, group_id: str) -> Optional[int]:
        """查询群组模式"""
        try:
            async with db_manager.get_connection(self.db_path) as conn:
                async with conn.execute(
                    "SELECT mode FROM group_mode WHERE group_id=?",
                    (group_id,)
                ) as cursor:
                    result = await cursor.fetchone()
                    return result if result else None
        except Exception as e:
            logger.error(f'查询群组模式出错: {e}')
            return None

    async def set_plugin_config(self, mode: int, plugin_name: str, enabled: bool) -> bool:
        """设置插件配置
        Args:
            mode: 模式（群组模式或私聊模式）
            plugin_name: 插件名称
            enabled: 是否启用
        Returns:
            bool: 是否设置成功
        """
        try:
            async with db_manager.get_connection(self.db_path) as conn:
                await conn.execute(
                    """INSERT INTO plugin_config (mode, plugin_name, enabled)
                    VALUES (?, ?, ?)
                    ON CONFLICT(mode, plugin_name) 
                    DO UPDATE SET enabled = ?""",
                    (mode, plugin_name, enabled, enabled)
                )
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f'设置插件配置出错: {e}')
            return False

    async def delete_plugin_config(self, mode: int, plugin_name: str) -> bool:
        """删除插件配置
        Args:
            mode: 模式（群组模式或私聊模式）
            plugin_name: 插件名称
        Returns:
            bool: 是否删除成功
        """
        try:
            async with db_manager.get_connection(self.db_path) as conn:
                await conn.execute(
                    """DELETE FROM plugin_config 
                    WHERE mode=? AND plugin_name=?""",
                    (mode, plugin_name)
                )
                await conn.commit()
                return True
        except Exception as e:
            logger.error(f'删除插件配置出错: {e}')
            return False

    async def query_plugin_config(self, mode: int, plugin_name: str) -> Optional[bool]:
        """查询插件配置
        Args:
            mode: 模式（群组模式或私聊模式）
            plugin_name: 插件名称
        Returns:
            Optional[bool]: 插件是否启用，None 表示未配置
        """
        try:
            async with db_manager.get_connection(self.db_path) as conn:
                async with conn.execute(
                    """SELECT enabled FROM plugin_config 
                    WHERE mode=? AND plugin_name=?""",
                    (mode, plugin_name)
                ) as cursor:
                    result = await cursor.fetchone()
                    return bool(result[0]) if result else None
        except Exception as e:
            logger.error(f'查询插件配置出错: {e}')
            return None

    async def list_plugin_configs(self) -> List[str]:
        """列出所有已配置的插件
        Returns:
            List[str]: 插件名称列表
        """
        try:
            async with db_manager.get_connection(self.db_path) as conn:
                async with conn.execute(
                    "SELECT DISTINCT plugin_name FROM plugin_config"
                ) as cursor:
                    results = await cursor.fetchall()
                    return [row[0] for row in results]
        except Exception as e:
            logger.error(f'列出插件出错: {e}')
            return []

    async def get_enabled_plugins(self, mode: int) -> List[str]:
        """获取指定模式下所有启用的插件
        Args:
            mode: 模式（群组模式或私聊模式）
        Returns:
            List[str]: 启用的插件名称列表
        """
        try:
            async with db_manager.get_connection(self.db_path) as conn:
                async with conn.execute(
                    """SELECT plugin_name FROM plugin_config 
                    WHERE mode=? AND enabled=1""",
                    (mode,)
                ) as cursor:
                    results = await cursor.fetchall()
                    return [row[0] for row in results]
        except Exception as e:
            logger.error(f'获取启用插件列表出错: {e}')
            return []

if __name__ == '__main__':
    import asyncio
    
    async def main():
        admin_server = DbAdminServer()
        
    asyncio.run(main())